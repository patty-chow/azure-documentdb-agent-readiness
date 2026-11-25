/**
 * Idempotent seed script for touchpoints collection.
 * - Checks seed marker in 'seed_metadata' collection; if present skips.
 * - Creates compound index { customerId: 1, timestamp: 1 }.
 * - Inserts synthetic events across multiple customers.
 */

require('dotenv').config();
const { getDb, getClient } = require('../src/db');

function randInt(min, max) {
  return Math.floor(Math.random() * (max - min + 1)) + min;
}

function randomTimestamp(daysBack) {
  const now = Date.now();
  const past = now - Math.floor(Math.random() * daysBack * 24 * 3600 * 1000);
  return new Date(past);
}

async function seed() {
  const client = getClient();
  await client.connect();
  const db = await getDb();

  const meta = db.collection('seed_metadata');
  const marker = await meta.findOne({ name: 'seed_customer_journey_v1' });
  if (marker) {
    console.log('Seed already applied; skipping.');
    await client.close();
    return;
  }

  const coll = db.collection('touchpoints');
  // Create compound index to support match + sort queries
  await coll.createIndex({ customerId: 1, timestamp: 1 }, { name: 'customer_timestamp_idx' });

  const channels = ['email', 'web', 'call', 'sms', 'app'];
  const eventTypes = ['view', 'click', 'add_to_cart', 'purchase', 'support_contact', 'cancel', 'login'];

  const customers = [];
  for (let i = 0; i < 10; i++) customers.push(`cust_${String(i+1).padStart(4,'0')}`);

  const docs = [];
  const eventsPerCustomer = 100; // 10 * 100 = 1000 events total

  for (const cid of customers) {
    for (let i = 0; i < eventsPerCustomer; i++) {
      const ev = {
        customerId: cid,
        timestamp: randomTimestamp(90),
        channel: channels[randInt(0, channels.length-1)],
        eventType: eventTypes[randInt(0, eventTypes.length-1)],
        metadata: { value: randInt(1, 1000) }
      };
      docs.push(ev);
    }
  }

  console.log(`Inserting ${docs.length} documents into touchpoints...`);
  await coll.insertMany(docs);

  await meta.insertOne({ name: 'seed_customer_journey_v1', createdAt: new Date() });
  console.log('Seed complete.');
  await client.close();
}

seed().catch(err => {
  console.error('Seed failed:', err);
  process.exit(1);
});
