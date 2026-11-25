const { MongoClient } = require('mongodb');
const uri = process.env.DOCUMENTDB_URI;

let client;
let dbName = process.env.DOCUMENTDB_DB || 'sample_healthcare_08';

async function getClient(){
  if (!client) {
    if (!uri) throw new Error('DOCUMENTDB_URI not set in environment');
    client = new MongoClient(uri, { maxPoolSize: 10 });
    await client.connect();
  }
  return client;
}

async function getDb(){
  const c = await getClient();
  return c.db(dbName);
}

module.exports = { getClient, getDb };
