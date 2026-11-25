const mongoose = require('mongoose');
require('dotenv').config();

const uri = process.env.DOCUMENTDB_URI;
if (!uri) {
  console.error('DOCUMENTDB_URI is not set in environment');
  process.exit(1);
}

// Connection options chosen per documentdb-connection guidance for a long-running server
const options = {
  // moderate pool sizes suitable for small demo servers
  maxPoolSize: 20,
  minPoolSize: 5,
  // timeouts
  connectTimeoutMS: 10000,
  socketTimeoutMS: 30000,
  // retry reads
  retryWrites: true,
  serverSelectionTimeoutMS: 5000,
};

let isConnected = false;

async function connect() {
  if (isConnected) return mongoose.connection;
  await mongoose.connect(uri, { ...options, dbName: 'sample_healthcare_15' });
  isConnected = true;
  return mongoose.connection;
}

module.exports = { connect, mongoose };
