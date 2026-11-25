const { orchestrateClaim } = require('./orchestrator');

async function run() {
  try {
    const res = await orchestrateClaim('claim-9001');
    console.log('Orchestration result:', JSON.stringify(res, null, 2));
    process.exit(0);
  } catch (err) {
    console.error('Orchestration failed', err);
    process.exit(1);
  }
}

run();
