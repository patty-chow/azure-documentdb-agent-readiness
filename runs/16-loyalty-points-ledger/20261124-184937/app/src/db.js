const mongoose = require('mongoose');
const dotenv = require('dotenv');
dotenv.config();

const uri = process.env.DOCUMENTDB_URI;
const dbName = process.env.DATABASE_NAME || 'sample_retail_16';

if (!uri) {
  console.error('DOCUMENTDB_URI is not set. Set it in the environment or .env file.');
}

async function connect() {
  if (mongoose.connection.readyState === 1) return mongoose.connection;
  return mongoose.connect(uri, {
    dbName,
    // recommended options
    maxPoolSize: 20,
    serverSelectionTimeoutMS: 10000,
    // TLS is enabled via the connection string for Azure DocumentDB
  });
}

module.exports = { connect, mongoose };
