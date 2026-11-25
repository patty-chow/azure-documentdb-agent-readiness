const express = require('express');
const bodyParser = require('body-parser');
const { connect } = require('./db');
const AuditEvent = require('./models/AuditEvent');

const app = express();
app.use(bodyParser.json());

app.post('/audit', async (req, res) => {
  try {
    const { paymentReference, stage, stageTimestamp, details, _id } = req.body;
    const doc = new AuditEvent({ _id, paymentReference, stage, stageTimestamp, details });
    await doc.save();
    res.status(201).json(doc);
  } catch (err) {
    res.status(400).json({ error: err.message });
  }
});

app.get('/timeline/:paymentReference', async (req, res) => {
  try {
    const timeline = await AuditEvent.getTimeline(req.params.paymentReference);
    res.json(timeline);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

const port = process.env.PORT || 3000;
(async () => {
  try {
    await connect();
    app.listen(port, () => {
      console.log(`Audit-trail sample listening on http://localhost:${port}`);
    });
  } catch (err) {
    console.error('Failed to start', err);
    process.exit(1);
  }
})();
