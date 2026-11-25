const mongoose = require('mongoose');
const dotenv = require('dotenv');
dotenv.config();

const uri = process.env.DOCUMENTDB_URI;
const dbName = process.env.DATABASE_NAME || 'sample_banking_16';

if (!uri) {
  console.error('DOCUMENTDB_URI not set in environment');
  process.exit(1);
}

let connected = false;

async function connect() {
  if (connected) return mongoose.connection;
  await mongoose.connect(uri, {
    dbName,
    // Use recommended defaults; leave pool sizing to environment unless tuned
    // per documentdb-connection guidance
  });
  connected = true;
  return mongoose.connection;
}

module.exports = { connect, mongoose };
