// CLI helper to run the pipeline once for a given applicationId
const { runForApplication } = require('./pipeline');
const { getClient } = require('./db');

async function cli() {
  const id = process.argv[2];
  if (!id) {
    console.error('Usage: node src/run_pipeline.js <applicationId>');
    process.exit(2);
  }
  try {
    const res = await runForApplication(id);
    console.log('Decision written:', res);
  } catch (e) {
    console.error('Run failed:', e);
    process.exit(1);
  } finally {
    try {
      const client = getClient();
      await client.close();
    } catch (e) {
      // ignore
    }
  }
}

if (require.main === module) cli();
