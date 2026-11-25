#!/usr/bin/env node
const { connect, disconnect } = require('./db');
const Account = require('./models/account');
const Journal = require('./models/journal');
const cron = require('node-cron');
const dotenv = require('dotenv');
dotenv.config();

const BATCH_SIZE = parseInt(process.env.BATCH_SIZE || '500', 10);
const CRON_SCHEDULE = process.env.CRON_SCHEDULE || '0 0 * * *';

async function ensureIndexes() {
  // Partial index on accounts for active interest-bearing accounts
  try {
    await Account.collection.createIndex(
      { status: 1, interestBearing: 1, accountNumber: 1 },
      { name: 'idx_active_interestBearing', partialFilterExpression: { status: 'active', interestBearing: true } }
    );
  } catch (err) {
    console.warn('Could not create accounts index:', err.message);
  }

  // Unique index on journal to avoid duplicate entries for same account+runDate
  try {
    await Journal.collection.createIndex(
      { accountId: 1, runDate: 1 },
      { name: 'uidx_account_runDate', unique: true }
    );
  } catch (err) {
    console.warn('Could not create journal index (may already exist):', err.message);
  }
}

function computeDailyAccrual(balance, annualRatePercent, days = 1) {
  // Simple interest for the day: balance * (APR/100) * days/365
  return (balance * (annualRatePercent / 100) * (days / 365));
}

async function runOnce() {
  await connect();
  await ensureIndexes();

  const filter = { status: 'active', interestBearing: true };
  const cursor = Account.find(filter).cursor();

  let batch = [];
  let processed = 0;
  const runDate = new Date();
  // Normalize runDate to UTC date midnight for dedupe consistency
  runDate.setUTCHours(0,0,0,0);

  for (let doc = await cursor.next(); doc != null; doc = await cursor.next()) {
    const amount = computeDailyAccrual(doc.balance, doc.interestRate, 1);
    const journalDoc = {
      accountId: doc._id,
      runDate,
      amount,
      createdAt: new Date()
    };
    batch.push({ insertOne: { document: journalDoc } });

    if (batch.length >= BATCH_SIZE) {
      // flush
      try {
        const res = await Journal.collection.bulkWrite(batch, { ordered: false });
        processed += batch.length;
      } catch (err) {
        console.error('bulkWrite batch error:', err.message);
      }
      batch = [];
    }
  }

  if (batch.length > 0) {
    try {
      const res = await Journal.collection.bulkWrite(batch, { ordered: false });
      processed += batch.length;
    } catch (err) {
      console.error('final bulkWrite error:', err.message);
    }
  }

  console.log(`Run completed. Processed ~${processed} accruals (attempted inserts).`);
  await disconnect();
}

async function main() {
  const once = process.argv.includes('--once');
  if (once) {
    await runOnce();
    return;
  }

  console.log(`Scheduling daily accrual job: ${CRON_SCHEDULE} (default midnight UTC). Use --once to run immediately.`);
  cron.schedule(CRON_SCHEDULE, async () => {
    console.log('Starting scheduled accrual run at', new Date().toISOString());
    try {
      await runOnce();
    } catch (err) {
      console.error('Scheduled run failed:', err);
    }
  }, { timezone: 'UTC' });
}

if (require.main === module) {
  main().catch(err => {
    console.error('Fatal error:', err);
    process.exit(2);
  });
}

module.exports = { computeDailyAccrual, runOnce };
