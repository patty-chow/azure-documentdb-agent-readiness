const { connect } = require('../src/db');
const { appendEventTransactional } = require('../src/ledger');
const { Balance } = require('../src/models');

async function seed() {
  await connect();
  // ensure balances collection has indexes
  await Balance.createIndexes();

  const accounts = ['acct-1', 'acct-2', 'acct-3'];
  console.log('Seeding accounts and events for:', accounts.join(', '));

  for (const acct of accounts) {
    // idempotent: create balance doc if missing
    const existing = await Balance.findOne({ accountId: acct });
    if (!existing) {
      await Balance.create({ accountId: acct, balance: 0, lifetimePoints: 0 });
      console.log('Created balance for', acct);
    } else {
      console.log('Balance exists for', acct);
    }

    // create 10 events each (5 earns, 5 redeems) but skip if events already exist for account
    // naive: check event count via Event collection
  }

  // Generate some transactional events
  const ops = [
    () => appendEventTransactional('acct-1', 'earn', 1200, { note: 'signup bonus' }),
    () => appendEventTransactional('acct-1', 'earn', 3000, { note: 'purchase' }),
    () => appendEventTransactional('acct-1', 'redeem', 200, { note: 'coupon' }),
    () => appendEventTransactional('acct-2', 'earn', 50, { note: 'small purchase' }),
    () => appendEventTransactional('acct-2', 'earn', 100, { note: 'promo' }),
    () => appendEventTransactional('acct-3', 'earn', 7000, { note: 'big purchase' }),
    () => appendEventTransactional('acct-3', 'redeem', 500, { note: 'redemption' })
  ];

  for (const fn of ops) {
    try {
      const res = await fn();
      console.log('Applied event:', res.accountId, res.type, res.amount);
    } catch (err) {
      console.log('Skipping event due to error:', err.message);
    }
  }

  console.log('Seed complete.');
  process.exit(0);
}

seed().catch(err => { console.error(err); process.exit(1); });
