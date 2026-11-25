const { getDb, clientPromise } = require('../src/db');

async function seed() {
  await clientPromise;
  const db = getDb();
  const coll = db.collection('transactions');

  // Create index for date+category
  await coll.createIndex({ date: 1, category: 1 });

  const sample = [
    { transactionId: 't1', merchant: 'Starbucks', amount: 5.5, date: new Date('2026-01-05'), category: null },
    { transactionId: 't2', merchant: 'Uber', amount: 23.7, date: new Date('2026-01-12') },
    { transactionId: 't3', merchant: 'Whole Foods', amount: 76.2, date: new Date('2026-02-02') },
    { transactionId: 't4', merchant: 'Delta Airlines', amount: 450.0, date: new Date('2026-02-15') },
    { transactionId: 't5', merchant: 'Spotify', amount: 9.99, date: new Date('2026-03-01'), category: '' },
    { transactionId: 't6', merchant: 'Employer Inc', amount: -2500.0, date: new Date('2026-03-05'), category: 'Income' }
  ];

  for (const tx of sample) {
    await coll.updateOne({ transactionId: tx.transactionId }, { $set: tx }, { upsert: true });
  }
  console.log('Seeded sample transactions');
  process.exit(0);
}

seed().catch(err => { console.error(err); process.exit(1); });
