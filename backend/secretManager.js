// backend/secretManager.js
const { SecretManagerServiceClient } = require('@google-cloud/secret-manager');
const client = new SecretManagerServiceClient();

/**
 * Fetches the value of a secret from Google Secret Manager.
 * @param {string} secretName The name of the secret to fetch.
 * @returns {Promise<string>} The secret value.
 */
async function getSecret(secretName) {
  try {
    const [version] = await client.accessSecretVersion({
      name: `projects/${process.env.GCP_PROJECT_ID}/secrets/${secretName}/versions/latest`,
    });
    const payload = version.payload.data.toString('utf8');
    console.log(`Successfully fetched secret: ${secretName}`);
    return payload;
  } catch (error) {
    console.error(`Failed to fetch secret: ${secretName}`, error);
    throw new Error(`Could not access the secret: ${secretName}. Please ensure it exists and the service account has the 'Secret Manager Secret Accessor' role.`);
  }
}

module.exports = { getSecret };
