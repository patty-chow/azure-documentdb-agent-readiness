const { MongoClient } = require('mongodb');
const dotenv = require('dotenv');
dotenv.config();

const uri = process.env.DOCUMENTDB_URI;
if (!uri) {
  console.error('DOCUMENTDB_URI is not set in the environment.');
}

let client;
async function getClient() {
  if (!client) {
    client = new MongoClient(uri, {
      // conservative pool settings for a sample app
      maxPoolSize: 10,
      minPoolSize: 0,
      connectTimeoutMS: 10000,
      socketTimeoutMS: 60000,
      // DocumentDB guidance: retryWrites=false is often recommended for this provider
      retryWrites: false,
    });
    await client.connect();
  }
  return client;
}

async function getDb() {
  const c = await getClient();
  return c.db('sample_retail_12');
}

// Create indexes needed by the sample (idempotent)
async function ensureIndexes() {
  const db = await getDb();
  const carts = db.collection('carts');
  // Compound index to support queries for unprocessed carts sorted by last activity
  await carts.createIndex({ customerId: 1, updatedAt: 1, processedAt: 1 }, { name: 'customer_updated_processed_idx' });
  // Sparse index on processedAt to quickly find documents where it's absent or null
  await carts.createIndex({ processedAt: 1 }, { name: 'processed_sparse_idx', sparse: true });
}

module.exports = { getClient, getDb, ensureIndexes };
