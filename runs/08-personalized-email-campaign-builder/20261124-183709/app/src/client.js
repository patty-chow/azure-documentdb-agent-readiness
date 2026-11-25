const { MongoClient } = require('mongodb');
const dotenv = require('dotenv');
dotenv.config();

const uri = process.env.DOCUMENTDB_URI;
if (!uri) {
  console.error('Missing DOCUMENTDB_URI in environment. See .env.example');
}

// Singleton MongoClient per documentdb-driver guidance
const client = new MongoClient(uri, {
  // sensible defaults; override via env if needed
  maxPoolSize: 50,
  retryWrites: true,
});
const clientPromise = client.connect();

module.exports = {
  client,
  clientPromise,
  getDb: (dbName = process.env.DB_NAME || 'sample_retail_08') => client.db(dbName),
};
