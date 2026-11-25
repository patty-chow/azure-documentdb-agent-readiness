require('dotenv').config();
const { MongoClient } = require('mongodb');

const uri = process.env.DOCUMENTDB_URI;
if (!uri) {
  console.error('DOCUMENTDB_URI is not set in the environment. See .env.example');
}

let client;

function getClient() {
  if (!client) {
    // Use defaults recommended by documentdb-connection skill; keep pool default
    client = new MongoClient(uri, {
      // recommended: retryReads true for transient errors
      retryReads: true,
      // don't set aggressive pool sizes in the sample
    });
  }
  return client;
}

async function getDb(dbName = process.env.DATABASE_NAME || 'sample_customer_360_09') {
  const c = getClient();
  if (!c.topology || !c.topology.isConnected()) {
    await c.connect();
  }
  return c.db(dbName);
}

module.exports = { getClient, getDb };
