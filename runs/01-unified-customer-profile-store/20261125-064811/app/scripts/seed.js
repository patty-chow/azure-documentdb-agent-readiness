const fs = require('fs');
const path = require('path');
const dbModule = require('../src/db');
const { createModel } = require('../src/models/customer');
const { upsertEvent } = require('../src/lib/upsert');

async function run() {
  const db = await dbModule.connect();
  const Customer = createModel(db);

  // Ensure indexes
  console.log('Ensuring indexes...');
  try {
    await Customer.createIndexes();
  } catch (err) {
    // Handle existing index conflicts non-destructively
    if (err && err.codeName === 'IndexKeySpecsConflict') {
      console.warn('IndexKeySpecsConflict: an index with the same key already exists with a different spec. Skipping index creation to avoid destructive changes.');
    } else {
      throw err;
    }
  }

  const file = path.join(__dirname, '..', 'sample-data', 'events.json');
  const raw = fs.readFileSync(file, 'utf8');
  const events = JSON.parse(raw);

  for (const ev of events) {
    console.log('Upserting event:', ev.source, ev.customerId);
    await upsertEvent(db, ev);
  }

  console.log('Seed complete.');
  process.exit(0);
}

run().catch(err => {
  console.error('Seed failed:', err);
  process.exit(1);
});
