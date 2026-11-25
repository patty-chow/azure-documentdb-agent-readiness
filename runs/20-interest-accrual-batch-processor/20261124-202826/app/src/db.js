const mongoose = require('mongoose');
const dotenv = require('dotenv');
dotenv.config();

const uri = process.env.DOCUMENTDB_URI;
const dbName = process.env.DB_NAME || 'sample_banking_20';

if (!uri) {
  console.error('DOCUMENTDB_URI is not set. See .env.example');
  process.exit(1);
}

let isConnected = false;

async function connect() {
  if (isConnected) return mongoose.connection;
  // Follow documentdb-connection guidance: singleton client and sensible defaults for a long-running process
  await mongoose.connect(uri, {
    dbName,
    // Keep defaults but enable retryReads; pool sizing left to environment
    retryWrites: true,
    // recommended options can be added if needed for production; leave defaults for sample
  });
  isConnected = true;
  return mongoose.connection;
}

async function disconnect() {
  if (!isConnected) return;
  await mongoose.disconnect();
  isConnected = false;
}

module.exports = { connect, disconnect };
