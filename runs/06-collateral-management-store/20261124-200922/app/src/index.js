require('dotenv').config();
const express = require('express');
const cors = require('cors');
const mongoose = require('mongoose');
const assetsRouter = require('./routes/assets');
const coverageRouter = require('./routes/coverage');

const app = express();
app.use(cors());
app.use(express.json());

app.use('/assets', assetsRouter);
app.use('/coverage', coverageRouter);

const PORT = process.env.PORT || 3000;

async function start() {
  const uri = process.env.DOCUMENTDB_URI;
  const dbName = process.env.DB_NAME || 'sample_banking_06';
  if (!uri) {
    console.error('DOCUMENTDB_URI is not set. See .env.example');
    process.exit(1);
  }

  // Use sensible defaults for a long-running OLTP server per documentdb-connection guidance
  await mongoose.connect(uri, {
    dbName,
    // Mongoose passes options through to the underlying driver
    serverSelectionTimeoutMS: 5000,
    socketTimeoutMS: 30000,
    // retryWrites is commonly disabled in SRV for some managed clusters; the environment-provided URI controls it
  });

  app.listen(PORT, () => {
    console.log(`Server listening on port ${PORT}`);
  });
}

if (require.main === module) {
  start().catch(err => {
    console.error('Failed to start:', err);
    process.exit(1);
  });
}

module.exports = app;
