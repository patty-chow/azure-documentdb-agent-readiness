#!/usr/bin/env node
const { getDb, getClient } = require('./db');
const orchestrator = require('./orchestrator');

async function run() {
  const client = await getClient();
  const db = await getDb();
  const coll = db.collection('events');
  console.log('Opening change stream on events collection...');
  const changeStream = coll.watch([], { fullDocument: 'updateLookup' });
  changeStream.on('change', async (change) => {
    // We only care about insert or replace or update that yields a qualifying event
    const doc = change.fullDocument;
    if (!doc) return;
    if (['cart_abandon', 'contract_renewal', 'birthday'].includes(doc.type)) {
      console.log('Change stream observed qualifying event:', doc.eventId, doc.type);
      try {
        await orchestrator.processEvent(doc);
      } catch (err) {
        console.error('Orchestration failed', err);
      }
    }
  });

  process.on('SIGINT', async () => {
    console.log('Shutting down...');
    await changeStream.close();
    await client.close();
    process.exit(0);
  });
}

if (require.main === module) run();
module.exports = { run };
