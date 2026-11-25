const express = require('express');
const bodyParser = require('body-parser');
const { connect, mongoose } = require('./db');
const Trade = require('./models/trade');
const startChangeStream = require('./watcher/changeStream');

const app = express();
app.use(bodyParser.json());

const PORT = process.env.PORT || 3000;

// Allowed transitions
const ALLOWED = {
  INIT: ['PENDING_SETTLEMENT','FAILED'],
  PENDING_SETTLEMENT: ['SETTLED','FAILED'],
  FAILED: [],
  SETTLED: []
};

app.post('/trades/:id/advance', async (req, res) => {
  const toState = req.body.toState;
  const by = req.body.by || 'system';
  const note = req.body.note || '';
  const tradeId = req.params.id;

  const session = await mongoose.startSession();
  try {
    await session.withTransaction(async () => {
      const trade = await Trade.findOne({ tradeId }).session(session);
      if (!trade) {
        res.status(404).json({ error: 'trade not found' });
        throw new Error('abort-transaction');
      }
      if (!ALLOWED[trade.currentState] || !ALLOWED[trade.currentState].includes(toState)) {
        res.status(400).json({ error: 'invalid state transition' });
        throw new Error('abort-transaction');
      }

      const transition = { from: trade.currentState, to: toState, by, note, at: new Date() };
      trade.currentState = toState;
      trade.stateHistory.push(transition);
      trade.version = (trade.version || 1) + 1;
      await trade.save({ session });

      // Optionally, write to an audit collection in same transaction (omitted for brevity)
      res.json({ trade });
    });
  } catch (err) {
    if (err.message === 'abort-transaction') {
      // response already sent
    } else {
      console.error('transaction failed', err);
      res.status(500).json({ error: 'transaction failed', detail: err.message });
    }
  } finally {
    session.endSession();
  }
});

app.get('/settlement-rates', async (req, res) => {
  // Aggregation: group by assetClass and counterparty, compute settled rate
  const pipeline = [
    { $group: { _id: { assetClass: '$assetClass', counterparty: '$counterparty' }, total: { $sum: 1 }, settled: { $sum: { $cond: [{ $eq: ['$currentState', 'SETTLED'] }, 1, 0] } } } },
    { $project: { assetClass: '$_id.assetClass', counterparty: '$_id.counterparty', total: 1, settled: 1, rate: { $cond: [{ $eq: ['$total', 0] }, 0, { $divide: ['$settled', '$total'] }] } } },
    { $sort: { assetClass: 1, counterparty: 1 } }
  ];
  try {
    const results = await Trade.aggregate(pipeline).exec();
    res.json(results);
  } catch (err) {
    console.error('aggregation error', err);
    res.status(500).json({ error: 'aggregation failed' });
  }
});

app.get('/seed', async (req, res) => {
  // invoke the script in-process for convenience
  try {
    const seed = require('../scripts/seed');
    await seed.run();
    res.json({ ok: true });
  } catch (err) {
    console.error('seed error', err);
    res.status(500).json({ error: 'seed failed', detail: err.message });
  }
});

(async function main() {
  try {
    await connect();
    // ensure indexes
    await Trade.collection.createIndex({ assetClass: 1, counterparty: 1, currentState: 1 });
    await Trade.collection.createIndex({ currentState: 1 });

    // start change stream watcher
    startChangeStream();

    app.listen(PORT, () => {
      console.log(`Server listening ${PORT}`);
    });
  } catch (err) {
    console.error('startup error', err);
    process.exit(1);
  }
})();
