const mongoose = require('mongoose');
const dotenv = require('dotenv');
dotenv.config();

const uri = process.env.DOCUMENTDB_URI;
const dbName = process.env.MONGODB_DATABASE || 'sample_banking_03';

if (!uri) {
  console.error('Missing DOCUMENTDB_URI in environment. Copy .env.example to .env and set DOCUMENTDB_URI');
}

let isConnected = false;

async function connect() {
  if (isConnected) return mongoose.connection;
  // Use sensible defaults for a long-running server per documentdb-connection guidance
  await mongoose.connect(uri, {
    dbName,
    autoIndex: false, // we will create indexes explicitly
    maxPoolSize: 50,
    minPoolSize: 10,
    serverSelectionTimeoutMS: 5000,
    retryWrites: true,
    // useNewUrlParser, useUnifiedTopology are defaults in Mongoose 7
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
