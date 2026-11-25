#!/usr/bin/env node
const { processReturn } = require('../src/orchestration');
const dotenv = require('dotenv');
dotenv.config();

async function run() {
  // Two scenarios using seeded orderIds
  const scenarios = [
    { orderId: 'ORD-001', reason: 'Too small / changed mind', requester: 'customer' },
    { orderId: 'ORD-002', reason: 'Defective', requester: 'customer' }
  ];

  for (const s of scenarios) {
    try {
      const res = await processReturn(s);
      console.log('Result for', s.orderId, JSON.stringify(res, null, 2));
    } catch (e) {
      console.error('Error processing', s.orderId, e.message);
    }
  }
  process.exit(0);
}

run().catch(e => { console.error(e); process.exit(1); });
