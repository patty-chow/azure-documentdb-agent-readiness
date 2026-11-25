const { MongoClient } = require('mongodb');
const dotenv = require('dotenv');
dotenv.config();

if (!process.env.DOCUMENTDB_URI) {
  throw new Error('DOCUMENTDB_URI must be set in environment');
}

// Singleton MongoClient per documentdb-driver guidance
const client = new MongoClient(process.env.DOCUMENTDB_URI, {
  // conservative defaults for a long-running server (OLTP)
  maxPoolSize: 50,
  minPoolSize: 10,
  retryWrites: true,
  tls: true,
});
const clientPromise = client.connect();

function getDb(name = 'sample_fintech_02') {
  return client.db(name);
}

module.exports = { client, clientPromise, getDb };
