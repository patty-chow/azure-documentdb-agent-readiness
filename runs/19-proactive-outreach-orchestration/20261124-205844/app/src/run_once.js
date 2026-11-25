#!/usr/bin/env node
const { getDb, getClient } = require('./db');
const orchestrator = require('./orchestrator');

async function main() {
  const client = await getClient();
  const db = await getDb();
  try {
    const events = await db.collection('events').find({ type: { $in: ['cart_abandon', 'contract_renewal', 'birthday'] } }).toArray();
    console.log('Found events to process:', events.length);
    for (const ev of events) {
      console.log('Processing', ev.eventId, ev.type);
      const res = await orchestrator.processEvent(ev);
      console.log('Processed result:', res && res.outreach && res.outreach.logId);
    }
  } catch (err) {
    console.error('run_once error', err);
  } finally {
    await client.close();
  }
}

if (require.main === module) main();
