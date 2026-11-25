require('dotenv').config();
const express = require('express');
const morgan = require('morgan');
const mongoose = require('mongoose');
const nearbyRouter = require('./routes/nearby');

const app = express();
app.use(morgan('dev'));
app.use(express.json());

app.use('/nearby', nearbyRouter);

const PORT = process.env.PORT || 3000;
const URI = process.env.DOCUMENTDB_URI;

if (!URI) {
  console.error('DOCUMENTDB_URI is not set. Copy .env.example to .env and set DOCUMENTDB_URI');
  process.exit(1);
}

mongoose.set('strictQuery', false);

mongoose.connect(URI, { dbName: 'sample_retail_20' })
  .then(() => {
    console.log('Connected to DocumentDB cluster');
    app.listen(PORT, () => {
      console.log(`Server listening on port ${PORT}`);
    });
  })
  .catch(err => {
    console.error('Failed to connect to DocumentDB:', err);
    process.exit(1);
  });
