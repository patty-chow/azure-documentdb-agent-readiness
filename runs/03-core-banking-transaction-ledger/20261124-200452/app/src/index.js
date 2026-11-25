const express = require('express');
const bodyParser = require('body-parser');
const dotenv = require('dotenv');
dotenv.config();

const { connect } = require('./db');
const Account = require('./models/account');
const Transaction = require('./models/transaction');
const { postTransaction } = require('./transactions');

const app = express();
app.use(bodyParser.json());

app.post('/transactions', async (req, res) => {
  try {
    const { accountId, amount, type, transactionRef, metadata } = req.body;
    const result = await postTransaction({ accountId, amount, type, transactionRef, metadata });
    res.status(201).json(result);
  } catch (err) {
    if (err && err.code === 11000) {
      return res.status(409).json({ error: 'duplicate', message: err.message, existing: err.existing });
    }
    console.error(err);
    res.status(500).json({ error: 'internal', message: err.message });
  }
});

app.get('/accounts/:id', async (req, res) => {
  try {
    const accountId = req.params.id;
    const account = await Account.findOne({ accountId }).lean();
    if (!account) return res.status(404).json({ error: 'not_found' });
    const recent = await Transaction.find({ accountId }).sort({ createdAt: -1 }).limit(10).lean();
    res.json({ account, recent });
  } catch (err) {
    console.error(err);
    res.status(500).json({ error: 'internal', message: err.message });
  }
});

async function ensureIndexes() {
  // Ensure model indexes are created before accepting writes
  await Transaction.init();
  await Account.init();
}

async function start() {
  await connect();
  await ensureIndexes();
  const port = process.env.PORT || 3000;
  app.listen(port, () => console.log('Server listening on', port));
}

if (require.main === module) {
  start().catch(err => {
    console.error('Failed to start', err);
    process.exit(1);
  });
}

module.exports = app;
