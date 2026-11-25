const { MongoClient } = require('mongodb');
const dotenv = require('dotenv');
dotenv.config();

const uri = process.env.DOCUMENTDB_URI;
if (!uri) {
  console.warn('DOCUMENTDB_URI not set. Some scripts may fail until it is provided.');
}

let client;

async function getClient() {
  if (client) return client;
  if (!uri) throw new Error('DOCUMENTDB_URI is not set');
  client = new MongoClient(uri, {
    // connection options tuned for DocumentDB: keep defaults but allow pooling
    maxPoolSize: 50,
    serverSelectionTimeoutMS: 5000
  });
  await client.connect();
  return client;
}

async function getDb() {
  const c = await getClient();
  return c.db('sample_fintech_18');
}

module.exports = { getClient, getDb };
