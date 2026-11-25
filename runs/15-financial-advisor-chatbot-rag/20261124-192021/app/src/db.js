const { MongoClient } = require('mongodb');

let client;

function getClient() {
  if (!client) {
    const uri = process.env.DOCUMENTDB_URI;
    if (!uri) throw new Error('DOCUMENTDB_URI environment variable is required');
    client = new MongoClient(uri, {
      // reasonable defaults; see documentdb-connection guidance for tuning
      retryReads: true,
      maxPoolSize: 50,
      minPoolSize: 0,
      connectTimeoutMS: 10000,
      socketTimeoutMS: 30000
    });
  }
  return client;
}

async function getDb(dbName = 'sample_fintech_15') {
  const c = getClient();
  if (!c.topology || !c.topology.isConnected()) {
    await c.connect();
  }
  return c.db(dbName);
}

module.exports = { getClient, getDb };
