const { getDb, client } = require('./db');

async function test() {
  try {
    const db = await getDb();
    const dblist = await db.admin().listDatabases();
    console.log('Connected. Target DB:', db.databaseName);
    const cols = await db.collections();
    console.log('Collections in target DB:', cols.map(c => c.collectionName));
  } catch (e) {
    console.error('Connection test failed:', e.message);
    process.exit(2);
  } finally {
    await client.close();
  }
}

if (require.main === module) test();
