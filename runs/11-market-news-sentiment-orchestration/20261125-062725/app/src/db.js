const { MongoClient } = require('mongodb');
const SAMPLE_DB = 'sample_fintech_11';
let client;

async function getClient(){
  if(client) return client;
  const uri = process.env.DOCUMENTDB_URI;
  if(!uri) throw new Error('DOCUMENTDB_URI not set');
  client = new MongoClient(uri);
  await client.connect();
  return client;
}

async function getDb(){
  const c = await getClient();
  return c.db(SAMPLE_DB);
}

module.exports = { getClient, getDb };
