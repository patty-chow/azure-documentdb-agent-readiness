const { MongoClient } = require('mongodb');
const dotenv = require('dotenv');
dotenv.config();

const uri = process.env.DOCUMENTDB_URI;
const dbName = process.env.DATABASE_NAME || 'sample_healthcare_05';

if (!uri) {
  throw new Error('DOCUMENTDB_URI environment variable is required. See .env.example');
}

let client;
let db;

async function getClient() {
  if (!client) {
    client = new MongoClient(uri, {
      // recommended defaults; allow the environment/cluster to negotiate TLS and auth
      maxPoolSize: 10,
      serverSelectionTimeoutMS: 5000,
    });
    await client.connect();
  }
  return client;
}

async function getDb() {
  if (!db) {
    const c = await getClient();
    db = c.db(dbName);
  }
  return db;
}

module.exports = { getClient, getDb };
