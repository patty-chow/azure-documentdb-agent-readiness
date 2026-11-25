require('dotenv').config();
const pino = require('pino');
const { getDb } = require('../src/db');

const log = pino();

async function seed() {
  const db = await getDb();
  const coll = db.collection('events');

  const sampleCustomers = ['alice', 'bob', 'carol', 'dan'];
  const ops = [];
  for (let i = 0; i < 200; i++) {
    const customerId = sampleCustomers[i % sampleCustomers.length];
    const eventId = `evt-${Math.floor(i/2)}`; // create duplicates on purpose
    const doc = {
      customerId,
      eventId,
      eventType: ['page_view', 'click', 'purchase'][i % 3],
      timestamp: new Date(),
      payload: { idx: i }
    };
    // upsert to keep idempotent seed
    ops.push({ updateOne: { filter: { customerId: doc.customerId, eventId: doc.eventId }, update: { $set: doc }, upsert: true } });
  }

  log.info({ count: ops.length }, 'Seeding events with upsert bulk ops (idempotent)');
  const res = await coll.bulkWrite(ops, { ordered: false });
  log.info({ result: res.result }, 'Seed complete');
}

seed().then(() => process.exit(0)).catch(err => { console.error(err); process.exit(1); });
