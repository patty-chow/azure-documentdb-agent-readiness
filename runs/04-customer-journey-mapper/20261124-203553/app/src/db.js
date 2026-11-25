require('dotenv').config();
const { MongoClient } = require('mongodb');

// Singleton MongoClient per documentdb-driver guidance
let _client = null;

// Connection settings chosen conservatively for a long-running sample server.
// Reasoning: small-to-moderate concurrency expected for a demo service.
// See documentdb-connection skill for tuning guidance.
const clientOptions = {
  maxPoolSize: process.env.MAX_POOL_SIZE ? parseInt(process.env.MAX_POOL_SIZE, 10) : 20,
  minPoolSize: process.env.MIN_POOL_SIZE ? parseInt(process.env.MIN_POOL_SIZE, 10) : 0,
  maxIdleTimeMS: process.env.MAX_IDLE_MS ? parseInt(process.env.MAX_IDLE_MS, 10) : 300000,
  connectTimeoutMS: 10000,
  socketTimeoutMS: 30000,
  retryWrites: true,
};

function getClient() {
  if (_client) return _client;
  const uri = process.env.DOCUMENTDB_URI;
  if (!uri) throw new Error('DOCUMENTDB_URI environment variable is required');
  _client = new MongoClient(uri, clientOptions);
  return _client;
}

async function getDb(dbName) {
  const client = getClient();
  if (!client.topology || !client.topology.isConnected()) {
    await client.connect();
  }
  const name = dbName || process.env.DOCUMENTDB_DB_NAME || 'sample_customer_360_04';
  return client.db(name);
}

module.exports = { getClient, getDb };
