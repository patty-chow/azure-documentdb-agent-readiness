const mongoose = require('mongoose');
const debug = require('debug')('db');

let isConnected = false;

async function connect() {
  if (isConnected) return mongoose;
  const uri = process.env.DOCUMENTDB_URI;
  if (!uri) throw new Error('DOCUMENTDB_URI environment variable is required');

  // Connection options informed by documentdb-connection skill and driver best practices
  const opts = {
    // Ensure we use the sample database required by the sample
    dbName: 'sample_fintech_03',
    // For long-running server sample (OLTP-like) pick moderate pool sizing
    maxPoolSize: 50,
    minPoolSize: 10,
    serverSelectionTimeoutMS: 5000,
    socketTimeoutMS: 30000,
    // DocumentDB requires TLS in production; the cluster's URI should include tls=true
    tls: true,
    // DocumentDB may not recommend retryWrites in all contexts; leave driver defaults
    retryWrites: false,
  };

  await mongoose.connect(uri, opts);
  isConnected = true;
  debug('mongoose connected');
  return mongoose;
}

module.exports = { connect, mongoose };
