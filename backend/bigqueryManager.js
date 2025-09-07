// backend/bigqueryManager.js
const { BigQuery } = require('@google-cloud/bigquery');
const bigquery = new BigQuery();

const datasetId = 'exports';
const tableId = 'provider_results';

/**
 * Ensures the BigQuery dataset and table exist, creating them if necessary.
 */
async function setupBigQuery() {
  try {
    // Check if the dataset exists, create it if not
    const [dataset] = await bigquery.dataset(datasetId).get({ autoCreate: true });
    console.log(`BigQuery dataset '${dataset.id}' is ready.`);

    // Define the schema for the audit trail table
    const schema = [
      { name: 'jobId', type: 'STRING', mode: 'NULLABLE' },
      { name: 'provider', type: 'STRING', mode: 'REQUIRED' },
      { name: 'testId', type: 'STRING', mode: 'NULLABLE' },
      { name: 'jiraKey', type: 'STRING', mode: 'NULLABLE' },
      { name: 'status', type: 'STRING', mode: 'REQUIRED' },
      { name: 'apiRequest', type: 'JSON', mode: 'NULLABLE' },
      { name: 'apiResponse', type: 'JSON', mode: 'NULLABLE' },
      { name: 'timestamp', type: 'TIMESTAMP', mode: 'REQUIRED' },
    ];

    // Check if the table exists, create it if not
    const [table] = await dataset.table(tableId).get({ autoCreate: true, schema });
    console.log(`BigQuery table '${table.id}' is ready.`);

  } catch (error) {
    console.error('Failed to set up BigQuery:', error);
    throw new Error('Could not initialize BigQuery for audit logging.');
  }
}

/**
 * Inserts a log entry into the BigQuery audit table.
 * @param {object} logData - The data to log.
 */
async function logExportEvent(logData) {
  const row = {
    provider: 'Jira',
    timestamp: new Date(),
    ...logData,
  };
  try {
    await bigquery.dataset(datasetId).table(tableId).insert([row]);
  } catch (error) {
    console.error('Failed to insert log into BigQuery:', error.errors ? JSON.stringify(error.errors, null, 2) : error);
    // Don't throw an error here, as logging failure shouldn't stop the main process.
    // In a production system, you might send this to a separate monitoring service.
  }
}

/**
 * Fetches all export events for a given job ID from BigQuery.
 * @param {string} jobId - The ID of the export job.
 * @returns {Promise<Array>} An array of log entry objects.
 */
async function getExportEvents(jobId) {
  try {
    const query = `SELECT * FROM \`${datasetId}.${tableId}\` WHERE jobId = @jobId ORDER BY timestamp`;
    const options = {
      query: query,
      params: { jobId: jobId },
    };
    const [rows] = await bigquery.query(options);
    return rows;
  } catch (error) {
    console.error(`Failed to fetch export events for job ${jobId}:`, error);
    throw new Error('Could not retrieve audit trail from BigQuery.');
  }
}

module.exports = { setupBigQuery, logExportEvent, getExportEvents };
