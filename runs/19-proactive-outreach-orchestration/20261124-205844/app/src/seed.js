#!/usr/bin/env node
const { getDb, getClient } = require('./db');
const { v4: uuidv4 } = require('uuid');

async function upsertCustomers(db) {
  const customers = [
    { customerId: 'cust-001', name: 'Alice Smith', email: 'alice@example.com', preferred_channel: 'email', profile: { loyaltyTier: 'gold', birthday: '1990-05-21' } },
    { customerId: 'cust-002', name: 'Bob Jones', email: 'bob@example.com', preferred_channel: 'sms', phone: '+15551230002', profile: { loyaltyTier: 'silver', birthday: '1985-09-10' } },
    { customerId: 'cust-003', name: 'Carol Lee', email: 'carol@example.com', preferred_channel: 'email', profile: { loyaltyTier: 'bronze', birthday: '1992-12-01' } }
  ];

  const coll = db.collection('customers');
  for (const c of customers) {
    await coll.updateOne({ customerId: c.customerId }, { $set: c }, { upsert: true });
  }
}

async function upsertEvents(db) {
  const now = new Date();
  const events = [
    { eventId: 'evt-001', customerId: 'cust-001', type: 'cart_abandon', timestamp: now, payload: { cartItems: ['SKU-RED-123', 'SKU-BLU-987'], total: 129.95 } },
    { eventId: 'evt-002', customerId: 'cust-002', type: 'contract_renewal', timestamp: now, payload: { contractId: 'ctr-555', renewalDate: new Date(now.getTime() + 3 * 24 * 3600 * 1000) } },
    { eventId: 'evt-003', customerId: 'cust-003', type: 'birthday', timestamp: now, payload: { birthday: '1992-12-01' } }
  ];

  const coll = db.collection('events');
  for (const e of events) {
    await coll.updateOne({ eventId: e.eventId }, { $set: e }, { upsert: true });
  }
}

async function createIndexes(db) {
  // simple indexes for query performance
  await db.collection('events').createIndex({ customerId: 1 });
  await db.collection('events').createIndex({ type: 1 });
  await db.collection('outreach_logs').createIndex({ eventId: 1 });
}

async function main() {
  const client = await getClient();
  const db = await getDb();
  try {
    await upsertCustomers(db);
    await upsertEvents(db);
    await createIndexes(db);
    console.log('Seeding complete.');
  } catch (err) {
    console.error('Seed failed', err);
  } finally {
    await client.close();
  }
}

if (require.main === module) {
  main();
}

module.exports = { upsertCustomers, upsertEvents };
