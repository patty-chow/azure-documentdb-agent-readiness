const { clientPromise } = require('./client');

async function run() {
  await clientPromise;
  const client = require('./client').client;
  const dbs = await client.db().admin().listDatabases();
  console.log('Databases on server (names):', dbs.databases.map(d=>d.name));
  const db = client.db(process.env.DB_NAME || 'sample_retail_08');
  const segCount = await db.collection('segments').countDocuments();
  console.log('segments count in', db.databaseName, segCount);
  const docs = await db.collection('segments').find({}).limit(20).toArray();
  console.log('sample docs:', docs);
  process.exit(0);
}

run().catch(e=>{console.error(e);process.exit(1);});
