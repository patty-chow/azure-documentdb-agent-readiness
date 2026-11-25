const express = require('express');
const morgan = require('morgan');
const dotenv = require('dotenv');
const { connect } = require('./db');
const Heartbeat = require('./models/heartbeat');
const { handleHeartbeat, recomputeSummary } = require('./logic/summaryUpdater');

dotenv.config();

const PORT = process.env.PORT || 3000;
const THRESHOLD = parseFloat(process.env.AVAILABILITY_THRESHOLD || process.env.AVAILABILITY || '0.95');

async function start() {
  await connect();
  const app = express();
  app.use(express.json());
  app.use(morgan('dev'));

  app.post('/heartbeat', async (req, res) => {
    try {
      const hb = await Heartbeat.create(req.body);
      await handleHeartbeat(hb, THRESHOLD);
      res.status(201).json(hb);
    } catch (err) {
      console.error(err);
      res.status(500).json({ error: String(err) });
    }
  });

  app.get('/summary', async (req, res) => {
    const Summary = require('./models/summary');
    const doc = await Summary.findOne({ _id: 'network_summary' });
    res.json(doc || {});
  });

  // Start a change stream watching new heartbeats to keep summary in sync
  const conn = require('mongoose').connection;
  const heartbeatColl = conn.collection('heartbeats');
  const changeStream = heartbeatColl.watch([], { fullDocument: 'updateLookup' });
  changeStream.on('change', async (change) => {
    if (change.operationType === 'insert' || change.operationType === 'update') {
      const doc = change.fullDocument;
      await handleHeartbeat({ atmId: doc.atmId, status: doc.status, timestamp: doc.timestamp }, THRESHOLD);
    }
  });

  app.listen(PORT, () => {
    console.log(`ATM monitor listening on ${PORT}`);
  });
}

if (require.main === module) {
  start().catch(err => { console.error(err); process.exit(1); });
}

module.exports = { start };
