require('dotenv').config();
const { MongoClient } = require('mongodb');

const uri = process.env.DOCUMENTDB_URI;
if (!uri) {
  console.warn('DOCUMENTDB_URI not set. Local tests will mock the DB.');
}

let client;

function getClient() {
  if (!client) {
    client = new MongoClient(uri, {
      // Conservative defaults for a long-running demo server per documentdb-connection
      maxPoolSize: 20,
      minPoolSize: 0,
      connectTimeoutMS: 10000,
      socketTimeoutMS: 30000,
      // Let the driver handle retryable reads
      retryReads: true,
    });
  }
  return client;
}

async function getDb(dbName = process.env.DB_NAME || 'sample_banking_07') {
  const c = getClient();
  if (!c.topology || !c.topology.isConnected()) {
    await c.connect();
  }
  return c.db(dbName);
}

module.exports = { getClient, getDb };
