const { MongoClient } = require('mongodb');
let client;
let clientPromise;

function getClient() {
  if (!client) {
    const uri = process.env.DOCUMENTDB_URI;
    if (!uri) throw new Error('DOCUMENTDB_URI is not set');
    client = new MongoClient(uri, {
      // sensible defaults; tune per documentdb-connection guidance
      minPoolSize: 0,
      maxPoolSize: 50,
      retryWrites: true,
      tls: true,
    });
    clientPromise = client.connect();
  }
  return { client, clientPromise };
}

async function getDb(dbName = 'sample_retail_12') {
  const { client, clientPromise } = getClient();
  await clientPromise;
  return client.db(dbName);
}

module.exports = { getClient, getDb };
