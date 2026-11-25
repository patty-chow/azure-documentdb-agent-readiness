const { MongoClient } = require('mongodb');
const dotenv = require('dotenv');
dotenv.config();

const uri = process.env.DOCUMENTDB_URI;
if (!uri) {
  console.error('DOCUMENTDB_URI not set in environment');
  process.exit(1);
}

let client;

async function getClient() {
  if (client && client.topology && client.topology.isConnected()) return client;
  client = new MongoClient(uri, {
    // DocumentDB guidance: enable TLS by default via connection string; set retryWrites=false
    retryWrites: false
  });
  await client.connect();
  return client;
}

async function getDb() {
  const c = await getClient();
  const dbName = process.env.DATABASE_NAME || 'sample_customer_360_14';
  return c.db(dbName);
}

module.exports = { getClient, getDb };
