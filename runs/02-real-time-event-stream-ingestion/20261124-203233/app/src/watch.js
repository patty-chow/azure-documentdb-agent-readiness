require('dotenv').config();
const pino = require('pino');
const { getDb } = require('./db');

const log = pino();

async function runWatcher() {
  const db = await getDb();
  const coll = db.collection('events');

  log.info('Starting change stream watcher on events collection...');

  const changeStream = coll.watch([], { fullDocument: 'updateLookup' });

  changeStream.on('change', change => {
    try {
      log.info({ change }, 'Change stream event');
      // Simulate downstream profile update job trigger
      if (change.operationType === 'insert' || change.operationType === 'update') {
        const doc = change.fullDocument;
        // lightweight simulated job enqueue
        log.info({ customerId: doc.customerId, eventType: doc.eventType }, 'Enqueued profile-update job');
      }
    } catch (err) {
      log.error({ err }, 'Error handling change event');
    }
  });

  changeStream.on('error', err => {
    log.error({ err }, 'Change stream error');
    process.exit(1);
  });
}

runWatcher().catch(err => {
  log.error({ err }, 'Watcher failed to start');
  process.exit(1);
});
