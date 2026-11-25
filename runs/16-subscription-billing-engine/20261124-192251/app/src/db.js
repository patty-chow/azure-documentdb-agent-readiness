require('dotenv').config();
const mongoose = require('mongoose');

const uri = process.env.DOCUMENTDB_URI;
const dbName = process.env.DATABASE_NAME || 'sample_fintech_16';

if (!uri) {
  console.error('DOCUMENTDB_URI is not set. Copy .env.example to .env and set DOCUMENTDB_URI');
  process.exit(1);
}

// Singleton connection per documentdb-driver guidance
let connection = null;

async function connect() {
  if (connection) return connection;
  connection = await mongoose.connect(uri, {
    dbName,
    // recommended options: small pool for sample; disable retryWrites as advised in docs
    maxPoolSize: 10,
    serverSelectionTimeoutMS: 5000,
    autoIndex: false,
    retryWrites: false
  });
  return connection;
}

module.exports = { connect, mongoose };
