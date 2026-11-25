const mongoose = require('mongoose');
const dotenv = require('dotenv');
dotenv.config();

const uri = process.env.DOCUMENTDB_URI;
if (!uri) {
  console.warn('DOCUMENTDB_URI not set — tests may mock mongoose.');
}

// Connection options — conservative defaults for a long-running Express server per documentdb-connection guidance
const options = {
  // reuse connections, keep pool size reasonable for demo
  maxPoolSize: 50,
  minPoolSize: 10,
  connectTimeoutMS: 10000,
  socketTimeoutMS: 30000,
  serverSelectionTimeoutMS: 5000,
  // retryWrites typically false for DocumentDB; leave driver default unless user-supplied in URI
  // Other options may be provided in the URI itself.
};

let connectionPromise = null;

function connect() {
  if (connectionPromise) return connectionPromise;
  if (!uri) return Promise.reject(new Error('DOCUMENTDB_URI not configured'));
  connectionPromise = mongoose.connect(uri, options).then(() => mongoose);
  return connectionPromise;
}

module.exports = { connect, mongoose };
