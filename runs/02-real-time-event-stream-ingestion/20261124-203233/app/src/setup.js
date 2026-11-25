const { getDb } = require('./db');
const pino = require('pino');
const log = pino();

async function ensureIndexes() {
  const db = await getDb();
  const coll = db.collection('events');
  log.info('Ensuring indexes on events collection...');
  await coll.createIndex({ customerId: 1, eventId: 1 }, { unique: true, name: 'customer_event_unique' });
  log.info('Index ensured: customer_event_unique');
}

ensureIndexes().then(() => {
  log.info('Setup complete');
  process.exit(0);
}).catch(err => {
  log.error({ err }, 'Setup failed');
  process.exit(1);
});
