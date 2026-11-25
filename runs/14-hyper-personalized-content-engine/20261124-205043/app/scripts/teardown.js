const { getClient } = require('../src/db');

const DB_NAME = 'sample_customer_360_14';

async function teardown() {
  const client = await getClient();
  const db = client.db(DB_NAME);
  await db.collection('profiles').drop().catch(()=>{});
  await db.collection('segments').drop().catch(()=>{});
  await db.collection('interactions').drop().catch(()=>{});
  await db.collection('content_pieces').drop().catch(()=>{});
  console.log('Dropped sample collections (if they existed).');
}

(async () => {
  try {
    await teardown();
  } catch (err) {
    console.error(err);
    process.exit(1);
  } finally {
    process.exit(0);
  }
})();
