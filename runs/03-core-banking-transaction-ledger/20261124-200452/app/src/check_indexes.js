const { connect, disconnect } = require('./db');
const mongoose = require('mongoose');
const Transaction = require('./models/transaction');

async function run() {
  await connect();
  console.log('Transaction indexes:');
  const idx = await Transaction.collection.indexes();
  console.log(JSON.stringify(idx, null, 2));
  await disconnect();
}

if (require.main === module) run().catch(err => { console.error(err); process.exit(1); });
