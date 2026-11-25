const mongoose = require('mongoose');
require('dotenv').config();

const uri = process.env.DOCUMENTDB_URI;
if (!uri) {
  throw new Error('Please set DOCUMENTDB_URI in environment');
}

let isConnected = false;

async function connect() {
  if (isConnected) return mongoose;
  // Chosen options follow documentdb-connection skill guidance for OLTP long-running server
  const options = {
    dbName: 'sample_retail_05',
    // moderate pool size for a sample server; adjust in production
    maxPoolSize: 20,
    minPoolSize: 0,
    connectTimeoutMS: 10000,
    socketTimeoutMS: 30000,
    tls: true,
    retryWrites: true,
    // use unified topology via current driver through mongoose
  };

  await mongoose.connect(uri, options);
  isConnected = true;
  return mongoose;
}

module.exports = { connect, mongoose };
