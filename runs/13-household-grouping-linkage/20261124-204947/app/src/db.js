require('dotenv').config();
const mongoose = require('mongoose');

const uri = process.env.DOCUMENTDB_URI;
const dbName = process.env.DATABASE_NAME || 'sample_customer_360_13';

if (!uri) {
  console.warn('DOCUMENTDB_URI not set; scripts may fail. Set it in .env or environment.');
}

// Singleton mongoose connection per process
let isConnected = false;

async function connect() {
  if (isConnected) return mongoose.connection;
  // Use recommended options for long-running server (OLTP sample):
  const opts = {
    dbName,
    // Mongoose passes options to the underlying driver; keep defaults but
    // enable retryReads and sensible pool size for an example server.
    maxPoolSize: 50,
    minPoolSize: 10,
    serverSelectionTimeoutMS: 5000,
    socketTimeoutMS: 30000,
    retryWrites: true,
    retryReads: true
  };
  await mongoose.connect(uri, opts);
  isConnected = true;
  return mongoose.connection;
}

module.exports = { connect, mongoose };
