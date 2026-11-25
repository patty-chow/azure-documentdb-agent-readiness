#!/usr/bin/env node
const { connect, disconnect } = require('../src/db');
const Account = require('../src/models/account');
const dotenv = require('dotenv');
dotenv.config();

async function seed(num = 100) {
  await connect();
  const ops = [];
  for (let i = 0; i < num; i++) {
    const accNum = `ACC-${String(i+1).padStart(4,'0')}`;
    const balance = Math.round((Math.random() * 10000 + 100) * 100) / 100; // 100..10100
    const rate = +( (Math.random() * 3) + 0.25 ).toFixed(3); // 0.25% .. 3.25%
    const status = Math.random() < 0.9 ? 'active' : 'closed';
    const interestBearing = Math.random() < 0.85;

    ops.push({
      updateOne: {
        filter: { accountNumber: accNum },
        update: { $set: { accountNumber: accNum, balance, interestRate: rate, status, interestBearing, updatedAt: new Date() } },
        upsert: true
      }
    });
  }

  try {
    const res = await Account.collection.bulkWrite(ops, { ordered: false });
    console.log('Seed completed:', res.result || res);
  } catch (err) {
    console.error('Seed error:', err);
  }

  await disconnect();
}

if (require.main === module) {
  const n = parseInt(process.argv[2] || process.env.SEED_COUNT || '100', 10);
  seed(n).catch(err => {
    console.error(err);
    process.exit(2);
  });
}

module.exports = seed;
