const { handleNewClaim } = require('./orchestrator');

async function run() {
  const payload = { claimId: 'c-1', transactionId: 't-1', reason: 'duplicate charge' };
  const result = await handleNewClaim(payload);
  console.log('Demo result:', JSON.stringify(result, null, 2));
}

run().catch(err => {
  console.error(err);
  process.exit(1);
});
