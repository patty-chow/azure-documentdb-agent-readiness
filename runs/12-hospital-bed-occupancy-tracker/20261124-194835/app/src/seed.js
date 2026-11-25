/**
 * Seed script: creates sample wards and beds idempotently.
 * Usage: DOCUMENTDB_URI set in env, then `node src/seed.js`
 */
require('dotenv').config();
const { connect, disconnect } = require('./db');
const Bed = require('./models/bed');
const WardSummary = require('./models/wardSummary');

const DEFAULT_TTL = parseInt(process.env.CLEANING_TTL_SECONDS || '300', 10);

async function ensureIndexes() {
  // TTL index on cleaningExpiresAt with expireAfterSeconds: 0 -> expire at the datetime value
  await Bed.collection.createIndex({ cleaningExpiresAt: 1 }, { expireAfterSeconds: 0 });
  // Additional indexes
  await Bed.collection.createIndex({ wardId: 1, status: 1 });
}

async function seed() {
  await connect();
  await ensureIndexes();

  const wards = [
    { wardId: 'ward-A', capacity: 6 },
    { wardId: 'ward-B', capacity: 8 },
    { wardId: 'ward-C', capacity: 5 }
  ];

  // Create wards summaries
  for (const w of wards) {
    await WardSummary.updateOne({ wardId: w.wardId }, { $setOnInsert: { capacity: w.capacity } }, { upsert: true });
  }

  // For idempotency, upsert beds by bedId
  for (const w of wards) {
    const count = w.capacity;
    for (let i = 1; i <= count; i++) {
      const bedId = `${w.wardId}-bed-${i}`;
      const status = i % 3 === 0 ? 'cleaning' : (i % 2 === 0 ? 'available' : 'occupied');
      const cleaningExpiresAt = status === 'cleaning' ? new Date(Date.now() + DEFAULT_TTL * 1000) : null;
      await Bed.updateOne({ bedId }, { $set: { wardId: w.wardId, status, lastStatusChangeAt: new Date(), cleaningExpiresAt } }, { upsert: true });
    }
  }

  // Recompute summaries from current beds (idempotent)
  for (const w of wards) {
    const counts = { occupied: 0, available: 0, cleaning: 0 };
    const beds = await Bed.find({ wardId: w.wardId }).lean();
    for (const b of beds) counts[b.status] = (counts[b.status] || 0) + 1;
    await WardSummary.updateOne({ wardId: w.wardId }, { $set: { counts } }, { upsert: true });
  }

  console.log('Seeding complete');
  await disconnect();
}

seed().catch(err => {
  console.error(err);
  process.exit(1);
});
