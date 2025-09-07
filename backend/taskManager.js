// backend/taskManager.js
const { CloudTasksClient } = require('@google-cloud/tasks');
const client = new CloudTasksClient();

const project = process.env.GCP_PROJECT_ID;
const location = process.env.GCP_REGION;
const queue = 'jira-export-queue'; // The name of your queue in Cloud Tasks
const processorUrl = process.env.JIRA_BATCH_PROCESSOR_URL;

if (!processorUrl) {
    throw new Error("FATAL: JIRA_BATCH_PROCESSOR_URL environment variable is not set. This is required for Cloud Tasks.");
}

/**
 * Creates a task to process a batch of Jira issues.
 * @param {Array} batch - An array of test case objects for Jira.
 * @returns {Promise<void>}
 */
async function createJiraBatchTask(batch) {
  const parent = client.queuePath(project, location, queue);

  const task = {
    httpRequest: {
      httpMethod: 'POST',
      url: processorUrl, // The URL of our /process-jira-batch endpoint
      headers: {
        'Content-Type': 'application/json',
      },
      body: Buffer.from(JSON.stringify(batch)).toString('base64'),
    },
  };

  try {
    console.log('Creating Cloud Task for batch...');
    const [response] = await client.createTask({ parent, task });
    console.log(`Created task ${response.name}`);
  } catch (error) {
    console.error('Error creating Cloud Task:', error);
    // In a real app, you'd want more robust error handling, maybe a retry or alert.
    throw new Error('Failed to create a batch processing task.');
  }
}

module.exports = { createJiraBatchTask };
