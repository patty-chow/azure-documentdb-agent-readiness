require('dotenv').config();
const express = require('express');
const { connect } = require('./db');
const Bed = require('./models/bed');
const WardSummary = require('./models/wardSummary');

const app = express();
app.use(express.json());

app.get('/wards/:wardId/summary', async (req, res) => {
  await connect();
  const wardId = req.params.wardId;
  const summary = await WardSummary.findOne({ wardId }).lean();
  if (!summary) return res.status(404).json({ error: 'Not found' });
  res.json(summary);
});

// Create or update bed status
app.post('/beds/:bedId/status', async (req, res) => {
  await connect();
  const bedId = req.params.bedId;
  const { wardId, status } = req.body;
  if (!wardId || !status) return res.status(400).json({ error: 'wardId and status required' });

  const update = { wardId, status, lastStatusChangeAt: new Date() };
  if (status === 'cleaning') {
    const ttlSec = parseInt(process.env.CLEANING_TTL_SECONDS || '300', 10);
    update.cleaningExpiresAt = new Date(Date.now() + ttlSec * 1000);
  } else {
    update.cleaningExpiresAt = null;
  }

  await Bed.updateOne({ bedId }, { $set: update }, { upsert: true });
  res.json({ ok: true });
});

const port = process.env.PORT || 3000;
app.listen(port, () => {
  console.log('Server listening on', port);
});

// Note: In production you'd run the change stream in a separate worker process. For the sample, users can run src/demo.js to see watcher in a short-lived process.
