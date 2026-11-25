require('dotenv').config();
const mongoose = require('mongoose');

// Singleton mongoose connection per documentdb-driver & documentdb-connection guidance
let isConnected = false;

async function connect() {
  if (isConnected) return mongoose;
  const uri = process.env.DOCUMENTDB_URI;
  if (!uri) throw new Error('DOCUMENTDB_URI environment variable is required');

  // Use explicit database name per run-environment guidance
  const opts = {
    // Mongoose will pass these to the underlying MongoClient
    maxPoolSize: 50,
    minPoolSize: 10,
    connectTimeoutMS: 10000,
    serverSelectionTimeoutMS: 5000,
    tls: true,
    dbName: 'sample_healthcare_03'
  };

  await mongoose.connect(uri, opts);
  isConnected = true;
  return mongoose;
}

module.exports = { connect };
