const { getDb, clientPromise } = require('../src/db');
const { categorizeTransaction } = require('../src/agent');

async function run() {
  await clientPromise;
  const db = getDb();
  const coll = db.collection('transactions');
  const cursor = coll.find({ $or: [ { category: { $exists: false } }, { category: null }, { category: '' } ] });
  let count = 0;
  while (await cursor.hasNext()) {
    const doc = await cursor.next();
    const category = await categorizeTransaction(doc);
    await coll.updateOne({ _id: doc._id }, { $set: { category } });
    count++;
    console.log(`Updated ${doc.transactionId} -> ${category}`);
  }
  console.log(`Categorized ${count} transactions`);
  process.exit(0);
}

run().catch(err => { console.error(err); process.exit(1); });
