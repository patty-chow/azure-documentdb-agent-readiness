const mongoose = require('mongoose');
const dotenv = require('dotenv');
dotenv.config();

const uri = process.env.DOCUMENTDB_URI;
if (!uri) {
  console.warn('DOCUMENTDB_URI not set; mongoose connect will fail until provided. Use .env or env vars.');
}

let connected = false;

async function connect() {
  if (connected) return mongoose.connection;
  // Mongoose creates a singleton internal connection. Use recommended options; DocumentDB guidance: retryWrites=false, tls enabled in the connection string
  await mongoose.connect(uri, {
    // Mongoose 7 defaults are okay; keep socket timeouts sensible
    serverSelectionTimeoutMS: 5000
  });
  connected = true;
  return mongoose.connection;
}

module.exports = { connect, mongoose };
