const { MongoClient } = require('mongodb');
require('dotenv').config();

const uri = process.env.DOCUMENTDB_URI;
if (!uri) throw new Error('DOCUMENTDB_URI not set in environment');

let client;
async function getClient() {
  if (!client) {
    // Use singleton client. Options left minimal; rely on URI settings.
    client = new MongoClient(uri, {
      // conservative defaults for a long-running server app
      retryWrites: false,
      // keep default pool sizing; change with care per documentdb-connection guidance
    });
    await client.connect();
  }
  return client;
}

async function getDb(dbName = process.env.DB_NAME || 'sample_customer_360_09') {
  const c = await getClient();
  return c.db(dbName);
}

module.exports = { getClient, getDb };
