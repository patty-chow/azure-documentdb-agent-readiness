require('dotenv').config();
const mongoose = require('mongoose');

const DATABASE_NAME = 'sample_banking_09';
const uri = process.env.DOCUMENTDB_URI;
if (!uri) {
  console.warn('DOCUMENTDB_URI not set; DB operations will fail until you set it in .env or environment');
}

let connectionPromise;

function connect() {
  if (!connectionPromise) {
    // OLTP defaults per documentdb-connection skill
    const opts = {
      dbName: DATABASE_NAME,
      // Mongoose passes these to the underlying driver
      maxPoolSize: 50,
      minPoolSize: 10,
      socketTimeoutMS: 30000,
      connectTimeoutMS: 10000,
      serverSelectionTimeoutMS: 5000,
      retryWrites: false
    };
    connectionPromise = mongoose.connect(uri, opts);
  }
  return connectionPromise;
}

module.exports = { connect, mongoose };
