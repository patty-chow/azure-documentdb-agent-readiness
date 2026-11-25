require('dotenv').config();
const mongoose = require('mongoose');

const uri = process.env.DOCUMENTDB_URI;
if (!uri) {
  throw new Error('DOCUMENTDB_URI environment variable is required');
}

// Use the database name explicitly per sample guidance
const DB_NAME = 'sample_retail_10';

let isConnected = false;

async function connect() {
  if (isConnected) return mongoose;
  // Use sensible defaults; leave pool tuning to the user.
  await mongoose.connect(uri, { dbName: DB_NAME, autoIndex: false });
  isConnected = true;
  return mongoose;
}

async function disconnect() {
  if (!isConnected) return;
  await mongoose.disconnect();
  isConnected = false;
}

module.exports = { connect, disconnect, mongoose };
