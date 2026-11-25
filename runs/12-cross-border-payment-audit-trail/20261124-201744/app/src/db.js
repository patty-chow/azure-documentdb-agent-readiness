const mongoose = require('mongoose');
const dotenv = require('dotenv');

dotenv.config();

const uri = process.env.DOCUMENTDB_URI;
if (!uri) {
  console.error('Missing DOCUMENTDB_URI in environment');
  process.exit(1);
}

const connect = async () => {
  // follow readiness guidance: use the given connection string and set dbName explicitly
  const conn = await mongoose.connect(uri, {
    dbName: 'sample_banking_12',
    // recommended options
    useNewUrlParser: true,
    useUnifiedTopology: true,
    // retryWrites is controlled by the connection string; do not force here
  });
  return conn;
};

module.exports = { connect, mongoose };
