const { connect, disconnect } = require('./db');
const Account = require('./models/account');
const Transaction = require('./models/transaction');

async function seed() {
  await connect();
  // Idempotent seeding: only insert accounts if they don't exist
  const accounts = [
    { accountId: 'acct-1', name: 'Alice', balance: 1000 },
    { accountId: 'acct-2', name: 'Bob', balance: 500 },
    { accountId: 'acct-3', name: 'Carol', balance: 0 }
  ];

  for (const a of accounts) {
    const existing = await Account.findOne({ accountId: a.accountId });
    if (existing) {
      console.log('Skipping existing', a.accountId);
    } else {
      await Account.create(a);
      console.log('Created account', a.accountId);
    }
  }

  // Ensure indexes
  await Transaction.init();
  await Account.init();

  console.log('Seed complete');
  await disconnect();
}

if (require.main === module) {
  seed().catch(err => { console.error(err); process.exit(1); });
}

module.exports = seed;
