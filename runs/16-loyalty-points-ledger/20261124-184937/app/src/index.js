const express = require('express');
const morgan = require('morgan');
const { connect } = require('./db');
const { Event, Balance } = require('./models');
const { appendEventTransactional } = require('./ledger');

const app = express();
app.use(morgan('dev'));
app.use(express.json());

app.get('/balance', async (req, res) => {
  const accountId = req.query.accountId;
  if (!accountId) return res.status(400).json({ error: 'accountId required' });
  try {
    // compute lifetimePoints via aggregation on events (sum of earns)
    const agg = await Event.aggregate([
      { $match: { accountId, type: 'earn' } },
      { $group: { _id: '$accountId', lifetimePoints: { $sum: '$amount' } } }
    ]);
    const lifetimePoints = agg.length ? agg[0].lifetimePoints : 0;

    // read balance doc
    const bal = await Balance.findOne({ accountId }).lean();
    const balance = bal ? bal.balance : 0;

    // derive tier from lifetimePoints
    let tier = 'bronze';
    if (lifetimePoints >= 5000) tier = 'gold';
    else if (lifetimePoints >= 1000) tier = 'silver';

    return res.json({ accountId, balance, lifetimePoints, tier });
  } catch (err) {
    console.error(err);
    return res.status(500).json({ error: 'internal' });
  }
});

app.get('/history', async (req, res) => {
  const accountId = req.query.accountId;
  if (!accountId) return res.status(400).json({ error: 'accountId required' });
  try {
    const docs = await Event.find({ accountId }).sort({ timestamp: 1 }).lean();
    return res.json(docs);
  } catch (err) {
    console.error(err);
    return res.status(500).json({ error: 'internal' });
  }
});

// for debug/demo only: create an event using transaction. Not exported in README as public API but useful for manual testing.
app.post('/event', async (req, res) => {
  const { accountId, type, amount } = req.body;
  if (!accountId || !type || typeof amount !== 'number') return res.status(400).json({ error: 'accountId,type,amount required' });
  try {
    const ev = await appendEventTransactional(accountId, type, amount, { source: 'api' });
    return res.json(ev);
  } catch (err) {
    return res.status(400).json({ error: err.message });
  }
});

async function main() {
  await connect();
  // ensure indexes
  await Event.createIndexes();
  await Balance.createIndexes();

  const port = process.env.PORT || 3000;
  app.listen(port, () => console.log(`Server listening on ${port}.`));
}

if (require.main === module) {
  main().catch(err => { console.error(err); process.exit(1); });
}

module.exports = app;
