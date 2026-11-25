require('dotenv').config();
const express = require('express');
const pino = require('pino');
const { addEvents } = require('./ingest');
const { getDb } = require('./db');

const log = pino();
const app = express();
app.use(express.json({ limit: '1mb' }));

app.get('/health', async (req, res) => {
  res.json({ status: 'ok' });
});

app.post('/events', async (req, res) => {
  const body = req.body;
  if (!body) return res.status(400).json({ error: 'empty body' });
  try {
    addEvents(body);
    res.status(202).json({ accepted: Array.isArray(body) ? body.length : 1 });
  } catch (err) {
    log.error({ err }, 'Failed to accept events');
    res.status(500).json({ error: 'failed to accept events' });
  }
});

const port = process.env.PORT || 3000;

// ensure indexes on startup
(async function main() {
  try {
    const db = await getDb();
    await db.collection('events').createIndex({ customerId: 1, eventId: 1 }, { unique: true, name: 'customer_event_unique' });
    log.info('Index ensured on startup');
  } catch (err) {
    log.error({ err }, 'Error ensuring index');
    process.exit(1);
  }

  app.listen(port, () => {
    log.info({ port }, 'Event ingestion service started');
  });
})();
