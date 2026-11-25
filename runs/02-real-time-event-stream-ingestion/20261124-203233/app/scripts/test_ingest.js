require('dotenv').config();
const { addEvents, flush } = require('../src/ingest');

async function run() {
  addEvents([{ customerId: 'alice', eventId: 'evt-test-1', eventType: 'click' }, { customerId: 'alice', eventId: 'evt-test-1', eventType: 'click' }]);
  // Wait a moment and flush explicitly
  await new Promise(r => setTimeout(r, 500));
  await flush();
  process.exit(0);
}

run().catch(err => { console.error(err); process.exit(1); });
