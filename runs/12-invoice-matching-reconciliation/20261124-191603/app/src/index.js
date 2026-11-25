const express = require('express');
require('dotenv').config();
const { connect } = require('./db');
const agent = require('./agent');
const { reconcileAll } = require('./reconcile');
const Invoice = require('./models/invoice');

const app = express();
app.use(express.json());

app.post('/reconcile/run', async (req, res) => {
  const sessionId = req.body.sessionId || 'default';
  try {
    await connect();
    const r = await reconcileAll(sessionId);
    res.json({ ok: true, results: r });
  } catch (e) {
    console.error(e);
    res.status(500).json({ ok: false, error: e.message });
  }
});

app.post('/reconcile/manual-correction', async (req, res) => {
  const { sessionId, invoiceNumber, matchedPoNumber } = req.body;
  if (!invoiceNumber || !matchedPoNumber) return res.status(400).json({ ok: false, error: 'invoiceNumber and matchedPoNumber required' });
  agent.addCorrection(sessionId || 'default', invoiceNumber, matchedPoNumber);
  res.json({ ok: true });
});

app.get('/reconcile/status', async (req, res) => {
  const invoiceNumber = req.query.invoiceNumber;
  if (!invoiceNumber) return res.status(400).json({ ok: false, error: 'invoiceNumber query required' });
  await connect();
  const inv = await Invoice.findOne({ invoiceNumber }).lean();
  res.json({ ok: true, invoice: inv });
});

if (require.main === module) {
  const port = process.env.PORT || 3000;
  connect().then(() => {
    app.listen(port, () => console.log(`Server listening ${port}`));
  }).catch(err => { console.error('DB connect failed', err); process.exit(1); });
}

module.exports = app;
