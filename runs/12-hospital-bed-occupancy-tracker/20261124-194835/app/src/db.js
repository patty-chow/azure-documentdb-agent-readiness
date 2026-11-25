const mongoose = require('mongoose');
const url = process.env.DOCUMENTDB_URI;

if (!url) {
  console.warn('DOCUMENTDB_URI not set; calls that connect will fail until it is provided.');
}

let connection = null;

async function connect() {
  if (connection) return connection;
  if (!url) throw new Error('DOCUMENTDB_URI environment variable is required');

  // Use recommended options for Azure DocumentDB (readiness guidance)
  connection = await mongoose.connect(url, {
    dbName: process.env.DB_NAME || 'sample_healthcare_12',
    // Mongoose 7 uses the underlying MongoDB driver; set serverSelectionTimeout to a reasonable value
    serverSelectionTimeoutMS: 5000,
    // The TLS/auth options are usually encoded in the connection string; keep retryWrites disabled by default
    // Other recommended options (if needed) can be provided in the URI
  });
  return connection;
}

async function disconnect() {
  if (!connection) return;
  await mongoose.disconnect();
  connection = null;
}

module.exports = { connect, disconnect, mongoose };
