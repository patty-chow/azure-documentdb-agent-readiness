require('dotenv').config();
const mongoose = require('mongoose');
const Interaction = require('../src/models/interaction');

const DB_NAME = 'sample_customer_360_06';
const MONGO_URI = process.env.DOCUMENTDB_URI;
if (!MONGO_URI) {
  console.error('DOCUMENTDB_URI is not set.');
  process.exit(1);
}

async function run() {
  await mongoose.connect(MONGO_URI, { dbName: DB_NAME, maxPoolSize: 5 });

  // Fetch history for cust-1
  console.log('=== HISTORY cust-1 (limit 2) ===');
  const items = await Interaction.find({ customerId: 'cust-1' }).sort({ timestamp: -1, _id: -1 }).limit(2).exec();
  console.log(items);

  // Channel breakdown overall
  console.log('=== CHANNEL BREAKDOWN ===');
  const breakdown = await Interaction.aggregate([ { $group: { _id: '$channel', count: { $sum: 1 } } }, { $project: { channel: '$_id', count: 1, _id: 0 } } ]).exec();
  console.log(breakdown);

  await mongoose.disconnect();
}

run().catch(err => { console.error(err); process.exit(1); });
