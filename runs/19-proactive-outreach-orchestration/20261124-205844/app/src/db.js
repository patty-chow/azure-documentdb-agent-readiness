const { MongoClient } = require('mongodb');
require('dotenv').config();

const uri = process.env.DOCUMENTDB_URI;
if (!uri) {
  console.error('DOCUMENTDB_URI not set. Copy .env.example to .env and set it.');
}

let client;
async function getClient() {
  if (!client) {
    client = new MongoClient(uri, {
      maxPoolSize: parseInt(process.env.MAX_POOL_SIZE || '20', 10),
      minPoolSize: parseInt(process.env.MIN_POOL_SIZE || '5', 10),
      retryWrites: true,
      connectTimeoutMS: 10000,
    });
    await client.connect();
  }
  return client;
}

async function getDb() {
  const c = await getClient();
  const dbName = process.env.DB_NAME || 'sample_customer_360_19';
  return c.db(dbName);
}

module.exports = { getClient, getDb };
