require('dotenv').config();
const { getDb } = require('../src/db');
const pino = require('pino');
const log = pino();

async function runOnce() {
  const db = await getDb();
  const coll = db.collection('events');

  const changeStream = coll.watch([], { fullDocument: 'updateLookup' });

  const onChange = change => {
    log.info({ change }, 'received change');
    changeStream.close().then(() => process.exit(0));
  };

  changeStream.on('change', onChange);
  changeStream.on('error', err => {
    log.error({ err }, 'change stream error');
    process.exit(2);
  });

  // Insert a test event to trigger the change stream
  const testDoc = { customerId: 'watcher', eventId: 'evt-watch-1', eventType: 'click', timestamp: new Date(), payload: {} };
  await coll.insertOne(testDoc);

  // safety timeout
  setTimeout(() => {
    log.error('Timeout waiting for change event');
    process.exit(3);
  }, 10000);
}

runOnce().catch(err => { console.error(err); process.exit(1); });
