const { connect, disconnect } = require('./db');
const { postTransaction } = require('./transactions');
const Account = require('./models/account');

async function demo() {
  await connect();

  const accountId = 'acct-1';
  console.log('Initial account:', await Account.findOne({ accountId }).lean());

  const txRef = 'demo-tx-1-' + Date.now();

  console.log('\nPosting credit +100');
  const res = await postTransaction({ accountId, amount: 100, type: 'credit', transactionRef: txRef, metadata: { note: 'demo credit' } });
  console.log('Result 1:', res.account.balance, 'txId:', res.transaction.transactionRef);

  console.log('\nAttempting duplicate post with same transactionRef (should be rejected)');
  try {
    await postTransaction({ accountId, amount: 100, type: 'credit', transactionRef: txRef, metadata: { note: 'duplicate' } });
    console.error('ERROR: duplicate allowed (unexpected)');
  } catch (err) {
    if (err && err.code === 11000) {
      console.log('Duplicate detected as expected. Account snapshot after duplicate attempt:', err.existing.account ? err.existing.account.balance : 'n/a');
    } else {
      console.error('Unexpected error', err);
    }
  }

  console.log('\nFinal account:', await Account.findOne({ accountId }).lean());
  await disconnect();
}

if (require.main === module) demo().catch(err => { console.error(err); process.exit(1); });
