const express = require('express');
const multer = require('multer');
const { Storage } = require('@google-cloud/storage');
const cors = require('cors');
const SseChannel = require('sse-channel');
const { exec } = require('child_process'); // To run the Python script
const fs = require('fs'); // To read the results file
const path = require('path'); // To handle file paths correctly
const { v4: uuidv4 } = require('uuid');
const { setupBigQuery, logExportEvent } = require('./bigqueryManager');
require('dotenv').config({ path: '../.env', quiet: true });

// Set credentials BEFORE any Google Cloud library is initialized
if (process.env.GCP_SERVICE_ACCOUNT_KEY_PATH) {
  process.env['GOOGLE_APPLICATION_CREDENTIALS'] = process.env.GCP_SERVICE_ACCOUNT_KEY_PATH;
  console.log('Using service account credentials from:', process.env.GCP_SERVICE_ACCOUNT_KEY_PATH);
} else {
  console.warn('Warning: GCP_SERVICE_ACCOUNT_KEY_PATH is not set. ADC will be used.');
}

const app = express();
const port = 3001;

// --- Middleware ---
app.use(cors());
app.use(express.json());
app.use(express.urlencoded({ extended: true }));

// --- Google Cloud Storage Setup ---
const storage = new Storage();
const bucketName = process.env.BUCKET_PREFIX + '-raw-documents';

// --- Multer Setup ---
const upload = multer({
  storage: multer.memoryStorage(),
  limits: { fileSize: 10 * 1024 * 1024 },
});

// --- SSE Channel Setup ---
const sseChannel = new SseChannel();

// --- Routes ---
app.get('/', (req, res) => {
  res.send('Backend server is running!');
});

app.post('/upload', upload.single('file'), (req, res) => {
  if (!req.file) {
    return res.status(400).send('No file uploaded.');
  }

  const bucket = storage.bucket(bucketName);
  const blob = bucket.file(req.file.originalname);
  const blobStream = blob.createWriteStream({ resumable: false });

  blobStream.on('error', (err) => {
    console.error('GCS Upload Error:', err);
    res.status(500).send({ message: 'Could not upload the file to GCS.', error: err });
  });

  blobStream.on('finish', () => {
    const publicUrl = `https://storage.googleapis.com/${bucket.name}/${blob.name}`;
    console.log(`File uploaded to GCS: ${publicUrl}`);
    
    // Start the real processing after upload is complete
    startProcessingPipeline(req.file.originalname);

    res.status(200).send({
      message: 'File uploaded successfully. Starting processing...',
      url: publicUrl,
    });
  });

  blobStream.end(req.file.buffer);
});

const { getSecret } = require('./secretManager');
const { createJiraBatchTask } = require('./taskManager');
const axios = require('axios');

app.get('/process', (req, res) => {
  sseChannel.addClient(req, res);
  console.log('Client connected for SSE.');
});

// The main endpoint that kicks off the batch export
app.post('/export-to-jira', async (req, res) => {
  const { testCases } = req.body;
  if (!testCases || !Array.isArray(testCases) || testCases.length === 0) {
    return res.status(400).json({ message: 'No test cases provided for export.' });
  }

  const jobId = uuidv4(); // Generate a unique ID for this entire export job
  console.log(`Received export request for ${testCases.length} test cases. Job ID: ${jobId}`);

  try {
    const batchSize = 50;
    const batches = [];
    for (let i = 0; i < testCases.length; i += batchSize) {
      const batch = testCases.slice(i, i + batchSize);
      batches.push({ jobId, batch }); // Pass jobId to each batch
    }
    console.log(`Split into ${batches.length} batches of up to ${batchSize} test cases each.`);

    for (const batchData of batches) {
      await createJiraBatchTask(batchData);
    }

    const initialUpdate = {
      status: 'export-started',
      message: `Export started for ${testCases.length} test cases.`,
      totalBatches: batches.length,
      totalTestCases: testCases.length,
      jobId: jobId,
    };
    sseChannel.send({ event: 'update', data: JSON.stringify(initialUpdate) });

    res.status(202).json({ message: 'Batch export process started.', jobId: jobId });

  } catch (error) {
    console.error('Failed to start Jira export process:', error);
    res.status(500).json({ message: 'Failed to start the export process.' });
  }
});

const { getExportEvents } = require('./bigqueryManager');
const archiver = require('archiver');
const Papa = require('papaparse');

// The new endpoint that Cloud Tasks will call to process each batch
app.post('/process-jira-batch', async (req, res) => {
  const { jobId, batch } = req.body;
  console.log(`Processing a batch of ${batch.length} test cases for Job ID: ${jobId}`);

  let jiraResponse = null;
  let apiRequestPayload = {};

  try {
    const jiraUrl = await getSecret('JIRA_URL');
    const jiraEmail = await getSecret('JIRA_EMAIL');
    const jiraApiToken = await getSecret('JIRA_API_TOKEN');
    const jiraProjectKey = await getSecret('JIRA_PROJECT_KEY');
    const jiraIssueType = await getSecret('JIRA_ISSUE_TYPE');

    const jiraIssues = batch.map(tc => ({
      fields: {
        project: { key: jiraProjectKey },
        summary: tc.title,
        description: {
          type: 'doc', version: 1,
          content: [{ type: 'paragraph', content: [{ type: 'text', text: tc.description || 'N/A' }] }],
        },
        issuetype: { name: jiraIssueType },
      },
    }));
    
    apiRequestPayload = { issueUpdates: jiraIssues };
    const authBuffer = Buffer.from(`${jiraEmail}:${jiraApiToken}`).toString('base64');
    const endpoint = `${jiraUrl}/rest/api/3/issue/bulk`;
    
    jiraResponse = await axios.post(endpoint, apiRequestPayload, {
      headers: {
        'Authorization': `Basic ${authBuffer}`,
        'Content-Type': 'application/json', 'Accept': 'application/json',
      },
    });

    const createdIssues = jiraResponse.data.issues.map((issue, index) => {
      const originalTestCase = batch[index];
      const logData = {
        jobId,
        testId: originalTestCase.test_case_id,
        jiraKey: issue.key,
        status: 'SUCCESS',
        apiRequest: JSON.stringify(apiRequestPayload.issueUpdates[index]),
        apiResponse: JSON.stringify(issue),
      };
      logExportEvent(logData); // Log success to BigQuery

      return {
        original_test_case_id: originalTestCase.test_case_id,
        id: issue.id,
        key: issue.key,
        link: `${jiraUrl}/browse/${issue.key}`,
      };
    });

    const batchUpdate = { status: 'batch-complete', issues: createdIssues, jobId };
    sseChannel.send({ event: 'update', data: JSON.stringify(batchUpdate) });

    console.log(`Successfully processed batch for Job ID: ${jobId}. Created ${createdIssues.length} Jira issues.`);
    res.status(200).send('Batch processed successfully.');

  } catch (error) {
    console.error(`Jira batch processing failed for Job ID: ${jobId}:`, error.response ? JSON.stringify(error.response.data, null, 2) : error.message);
    
    // Log failure for each test case in the batch
    batch.forEach((tc, index) => {
      const logData = {
        jobId,
        testId: tc.test_case_id,
        status: 'FAILURE',
        apiRequest: JSON.stringify(apiRequestPayload.issueUpdates ? apiRequestPayload.issueUpdates[index] : {}),
        apiResponse: JSON.stringify(error.response ? error.response.data : { error: error.message }),
      };
      logExportEvent(logData);
    });

    const batchErrorUpdate = { status: 'batch-error', message: 'A batch failed to process.', error: error.message, jobId };
    sseChannel.send({ event: 'update', data: JSON.stringify(batchErrorUpdate) });
    
    res.status(500).send('Failed to process batch.');
  }
});

app.post('/download-evidence/:jobId', async (req, res) => {
    const { jobId } = req.params;
    const { testCases } = req.body;

    if (!testCases || !Array.isArray(testCases)) {
        return res.status(400).json({ message: 'Test case data is required.' });
    }

    try {
        console.log(`[Evidence] Generating bundle for Job ID: ${jobId}`);
        const auditLogs = await getExportEvents(jobId);
        console.log(`[Evidence] Found ${auditLogs.length} audit logs.`);

        if (auditLogs.length === 0) {
            return res.status(404).json({ message: 'No audit trail found.' });
        }

        res.setHeader('Content-Type', 'application/zip');
        res.setHeader('Content-Disposition', `attachment; filename=evidence-bundle-${jobId}.zip`);

        const archive = archiver('zip', { zlib: { level: 9 } });
        archive.on('warning', (err) => {
            console.warn('[Evidence] Archiver warning:', err);
        });
        archive.on('error', (err) => {
            console.error('[Evidence] Archiver error:', err);
            // We can't send headers anymore if the stream has started, but logging is crucial.
        });
        archive.pipe(res);

        console.log('[Evidence] Appending original test cases...');
        archive.append(JSON.stringify(testCases, null, 2), { name: 'original_test_cases.json' });

        console.log('[Evidence] Appending Jira API responses...');
        archive.append(JSON.stringify(auditLogs, null, 2), { name: 'jira_api_responses.json' });

        console.log('[Evidence] Generating traceability matrix...');
        const traceabilityData = auditLogs.map(log => ({
            test_case_id: log.testId,
            export_status: log.status,
            jira_key: log.jiraKey || 'N/A',
            timestamp: log.timestamp ? log.timestamp.value : 'N/A',
        }));
        
        console.log('[Evidence] Unparsing CSV data...');
        const traceabilityCsv = Papa.unparse(traceabilityData);
        
        console.log('[Evidence] Appending traceability matrix...');
        archive.append(traceabilityCsv, { name: 'traceability_matrix.csv' });

        console.log('[Evidence] Finalizing archive...');
        await archive.finalize();
        console.log(`[Evidence] Successfully streamed bundle for Job ID: ${jobId}`);

    } catch (error) {
        console.error(`[Evidence] FAILED to generate bundle for Job ID: ${jobId}:`, error);
        // Check if headers have been sent
        if (!res.headersSent) {
            res.status(500).send('Failed to generate evidence bundle.');
        }
    }
});

// --- Processing Logic ---
async function startProcessingPipeline(filename) {
  const sendUpdate = (status, message) => {
    console.log(`Sending SSE event: ${message} - ${status}`);
    sseChannel.send({ event: 'update', data: JSON.stringify({ status, message }) });
  };

  try {
    // Step 1: Parsing Requirements (simulated as part of the main script)
    sendUpdate('inprogress', 'Parsing Requirements');
    await new Promise(resolve => setTimeout(resolve, 1000)); // Visual delay
    sendUpdate('success', 'Parsing Requirements');

    // Step 2: Searching Knowledge Base (simulated as part of the main script)
    sendUpdate('inprogress', 'Searching Compliance Knowledge Base');
    await new Promise(resolve => setTimeout(resolve, 1000)); // Visual delay
    sendUpdate('success', 'Searching Compliance Knowledge Base');

    // Step 3: Generating Test Cases (running the actual Python script)
    sendUpdate('inprogress', 'Generating Test Cases');
    
    // IMPORTANT: We assume the python command is in the system's PATH.
    // The script is run from the root of the project.
    const pythonScriptPath = path.join(__dirname, '..', 'main_pipeline.py');
    const projectRoot = path.join(__dirname, '..');

    console.log(`Executing Python script: python ${pythonScriptPath}`);
    await new Promise((resolve, reject) => {
      exec(`python ${pythonScriptPath}`, { cwd: projectRoot }, (error, stdout, stderr) => {
        if (error) {
          console.error(`Python script error: ${error.message}`);
          console.error(`stderr: ${stderr}`);
          sendUpdate('error', 'Generating Test Cases');
          reject(error);
          return;
        }
        console.log(`stdout: ${stdout}`);
        sendUpdate('success', 'Generating Test Cases');
        resolve();
      });
    });

    // Step 4: Reading results and sending to frontend
    const resultsPath = path.join(projectRoot, 'healthcare_qa_results.json');
    console.log(`Reading results from: ${resultsPath}`);
    const results = JSON.parse(fs.readFileSync(resultsPath, 'utf8'));

    console.log('Broadcasting final results...');
    sseChannel.send({
      event: 'update',
      data: JSON.stringify({
        status: 'complete',
        message: 'Processing Complete',
        results: results,
      }),
    });

  } catch (error) {
    console.error('Pipeline processing failed:', error);
    sseChannel.send({
      event: 'update',
      data: JSON.stringify({
        status: 'error',
        message: 'An error occurred during processing.',
      }),
    });
  }
}

// --- Server Start ---
app.listen(port, async () => {
  console.log(`Server listening at http://localhost:${port}`);
  try {
    await setupBigQuery(); // Ensure BigQuery is ready on startup
    console.log('BigQuery audit trail is configured.');
  } catch (error) {
    console.error('Server failed to start due to BigQuery setup error:', error);
    process.exit(1);
  }
});
