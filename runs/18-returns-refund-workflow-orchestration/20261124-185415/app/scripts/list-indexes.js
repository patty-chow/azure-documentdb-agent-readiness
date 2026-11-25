#!/usr/bin/env node
const { connect, mongoose } = require('../src/db');
const Order = require('../src/models/order');
const Return = require('../src/models/return');

async function list() {
  await connect();
  const oIdx = await Order.collection.indexes();
  const rIdx = await Return.collection.indexes();
  console.log('orders indexes:', JSON.stringify(oIdx, null, 2));
  console.log('returns indexes:', JSON.stringify(rIdx, null, 2));
  process.exit(0);
}

list().catch(e => { console.error(e); process.exit(1); });
