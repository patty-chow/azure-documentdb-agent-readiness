const express = require('express');
const { getDb, clientPromise } = require('./db');
const { categorizeTransaction } = require('./agent');

const app = express();
app.use(express.json());

app.get('/monthly-spend', async (req, res) => {
  await clientPromise;
  const db = getDb();
  const coll = db.collection('transactions');
  const pipeline = [
    { $match: { amount: { $exists: true } } },
    { $addFields: { ym: { $dateToString: { format: '%Y-%m', date: '$date' } } } },
    { $group: { _id: { ym: '$ym', category: '$category' }, total: { $sum: '$amount' } } },
    { $group: { _id: '$_id.ym', categories: { $push: { category: '$_id.category', total: '$total' } } } },
    { $sort: { _id: 1 } }
  ];
  const rows = await coll.aggregate(pipeline).toArray();
  res.json(rows.map(r => ({ month: r._id, categories: r.categories })));
});

// Trigger categorization over uncategorized transactions
app.post('/run-categorization', async (req, res) => {
  await clientPromise;
  const db = getDb();
  const coll = db.collection('transactions');
  const cursor = coll.find({ $or: [ { category: { $exists: false } }, { category: null }, { category: '' } ] }).limit(200);
  let count = 0;
  while (await cursor.hasNext()) {
    const doc = await cursor.next();
    const category = await categorizeTransaction(doc);
    await coll.updateOne({ _id: doc._id }, { $set: { category } });
    count++;
  }
  res.json({ categorized: count });
});

const port = process.env.PORT || 3000;
app.listen(port, () => console.log(`Server listening on ${port}`));
