require('dotenv').config();
const mongoose = require('mongoose');
const fs = require('fs');
const path = require('path');
const Interaction = require('../src/models/interaction');

const DB_NAME = 'sample_customer_360_06';
const MONGO_URI = process.env.DOCUMENTDB_URI;
if (!MONGO_URI) {
  console.error('DOCUMENTDB_URI is not set. Copy .env.example to .env and set it.');
  process.exit(1);
}

async function run() {
  await mongoose.connect(MONGO_URI, {
    dbName: DB_NAME,
    // keep small pool for one-shot seed script
    maxPoolSize: 5,
    minPoolSize: 0
  });

  // ensure indexes
  await Interaction.syncIndexes();

  const data = JSON.parse(fs.readFileSync(path.join(__dirname, '..', 'data', 'sample-data.json')));
  for (const doc of data) {
    await Interaction.updateOne({ interactionId: doc.interactionId }, { $set: doc }, { upsert: true });
    console.log('Upserted', doc.interactionId);
  }

  console.log('Seed complete.');
  await mongoose.disconnect();
}

run().catch(err => {
  console.error('Seed failed:', err);
  process.exit(1);
});
