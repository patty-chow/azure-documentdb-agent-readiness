require('dotenv').config();
const { MongoClient } = require('mongodb');
const pino = require('pino');
const log = pino();

const uri = process.env.DOCUMENTDB_URI;
const defaultDbName = process.env.DATABASE_NAME || 'sample_customer_360_02';

if (!uri) {
  log.error('DOCUMENTDB_URI is not set. Copy .env.example to .env and fill the connection string.');
  process.exit(1);
}

// Singleton MongoClient per documentdb-driver guidance
let client;
let clientPromise;

function getClient() {
  if (!client) {
    client = new MongoClient(uri, {
      // conservative defaults for a long-running server (OLTP)
      // these can be tuned via env in real apps
      maxPoolSize: process.env.MAX_POOL_SIZE ? parseInt(process.env.MAX_POOL_SIZE, 10) : 50,
      retryWrites: true,
      // ensure TLS is used (DocumentDB requires it in connection string), driver will honor the URI
    });
    clientPromise = client.connect();
  }
  return { client, clientPromise };
}

async function getDb(name) {
  const { client, clientPromise } = getClient();
  await clientPromise;
  return client.db(name || defaultDbName);
}

module.exports = { getClient, getDb, defaultDbName };
