const mongoose = require('mongoose');
require('dotenv').config();

const URI = process.env.DOCUMENTDB_URI;
if (!URI) {
  console.error('DOCUMENTDB_URI is not set. Set it in your environment or .env file.');
  process.exit(1);
}

let mainConnection;
let db;

async function connect() {
  if (mainConnection) return db;
  // Connect to the cluster (no DB selected) and then use the named DB sample_customer_360_01
  mainConnection = await mongoose.connect(URI, {
    // Mongoose 7 defaults are suitable for MongoDB 7.0; avoid hardcoding tls/ssl flags here.
    // The URI provided at runtime should include required options.
  });
  db = mongoose.connection.useDb('sample_customer_360_01');
  return db;
}

module.exports = { connect };
