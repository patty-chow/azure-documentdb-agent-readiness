require('dotenv').config();
const mongoose = require('mongoose');
const Store = require('../src/models/store');

const URI = process.env.DOCUMENTDB_URI;
if (!URI) {
  console.error('DOCUMENTDB_URI not set. Copy .env.example to .env and set DOCUMENTDB_URI');
  process.exit(1);
}

const seedData = [
  { name: 'Downtown Store', location: { type: 'Point', coordinates: [-122.4194, 37.7749] }, opening_hours: [{ day: 'Mon', open: '09:00', close: '18:00' }], stock: { 'sku-apple': 10, 'sku-banana': 5 } },
  { name: 'Uptown Store', location: { type: 'Point', coordinates: [-122.4313, 37.7739] }, opening_hours: [{ day: 'Tue', open: '09:00', close: '17:00' }], stock: { 'sku-apple': 0, 'sku-orange': 8 } },
  { name: 'Market Street', location: { type: 'Point', coordinates: [-122.4089, 37.7837] }, opening_hours: [{ day: 'Wed', open: '10:00', close: '19:00' }], stock: { 'sku-banana': 2 } },
  { name: 'Bay Area Outlet', location: { type: 'Point', coordinates: [-122.4014, 37.7890] }, opening_hours: [{ day: 'Thu', open: '08:00', close: '16:00' }], stock: { 'sku-apple': 3 } },
  { name: 'Mission Store', location: { type: 'Point', coordinates: [-122.4192, 37.7599] }, opening_hours: [{ day: 'Fri', open: '09:00', close: '18:00' }], stock: { 'sku-banana': 7 } }
];

async function run() {
  await mongoose.connect(URI, { dbName: 'sample_retail_20' });
  console.log('Connected for seeding');

  // Upsert each store by name
  for (const s of seedData) {
    await Store.updateOne({ name: s.name }, { $set: s }, { upsert: true });
    console.log('Upserted', s.name);
  }

  // Ensure indexes
  await Store.createIndexes();
  console.log('Indexes ensured');

  await mongoose.disconnect();
  console.log('Seed finished');
}

run().catch(err => {
  console.error('Seed failed:', err);
  process.exit(1);
});
