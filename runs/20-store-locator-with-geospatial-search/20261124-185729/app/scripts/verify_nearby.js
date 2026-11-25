require('dotenv').config();
const mongoose = require('mongoose');
const Store = require('../src/models/store');

const URI = process.env.DOCUMENTDB_URI;
if (!URI) {
  console.error('DOCUMENTDB_URI not set. Copy .env.example to .env and set DOCUMENTDB_URI');
  process.exit(1);
}

async function run() {
  await mongoose.connect(URI, { dbName: 'sample_retail_20' });
  console.log('Connected for verify script');

  const lat = parseFloat(process.argv[2] || '37.7749');
  const lon = parseFloat(process.argv[3] || '-122.4194');
  const radius = parseFloat(process.argv[4] || '5000');

  const pipeline = [
    { $geoNear: { near: { type: 'Point', coordinates: [lon, lat] }, distanceField: 'distanceMeters', spherical: true, maxDistance: radius } },
    { $project: { name: 1, distanceMeters: 1, opening_hours: 1, stock: 1 } }
  ];

  const results = await Store.aggregate(pipeline).exec();
  console.log('Nearby results:', JSON.stringify(results, null, 2));

  await mongoose.disconnect();
}

run().catch(err => {
  console.error('Verify failed:', err);
  process.exit(1);
});
