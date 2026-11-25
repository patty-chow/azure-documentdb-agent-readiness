const pino = require('pino');
const { getDb } = require('./db');
const log = pino();

const BATCH_SIZE = process.env.EVENTS_BATCH_SIZE ? parseInt(process.env.EVENTS_BATCH_SIZE, 10) : 1000;
const FLUSH_INTERVAL_MS = process.env.EVENTS_FLUSH_INTERVAL_MS ? parseInt(process.env.EVENTS_FLUSH_INTERVAL_MS, 10) : 2000;

let buffer = [];
let timer = null;
let flushing = false;

function startFlushTimer() {
  if (timer) return;
  timer = setInterval(() => {
    flush().catch(err => log.error({ err }, 'Periodic flush failed'));
  }, FLUSH_INTERVAL_MS);
}

function stopFlushTimer() {
  if (timer) {
    clearInterval(timer);
    timer = null;
  }
}

async function flush() {
  if (flushing) return;
  if (buffer.length === 0) return;
  flushing = true;
  const ops = buffer.splice(0, buffer.length);
  try {
    const db = await getDb();
    const coll = db.collection('events');
    // Prepare unordered insert ops
    const bulkOps = ops.map(ev => ({ insertOne: { document: ev } }));
    log.info({ count: bulkOps.length }, 'Flushing bulk ops');
    // unordered for throughput; duplicates will fail individually
    const res = await coll.bulkWrite(bulkOps, { ordered: false });
    log.info({ result: res.result }, 'Bulk write result');
  } catch (err) {
    // BulkWriteError may contain writeErrors; log and continue
    log.error({ err }, 'Bulk write failed');
  } finally {
    flushing = false;
  }
}

function addEvents(events) {
  if (!Array.isArray(events)) events = [events];
  for (const ev of events) {
    // normalize minimal shape
    const doc = Object.assign({
      customerId: ev.customerId || 'unknown',
      eventId: ev.eventId || `${Date.now()}-${Math.random().toString(36).slice(2,8)}`,
      eventType: ev.eventType || 'unknown',
      timestamp: ev.timestamp ? new Date(ev.timestamp) : new Date(),
      payload: ev.payload || {}
    }, ev);
    buffer.push(doc);
    if (buffer.length >= BATCH_SIZE) {
      // trigger async flush but don't await
      flush().catch(err => log.error({ err }, 'Flush triggered by batch size failed'));
    }
  }
  startFlushTimer();
}

module.exports = { addEvents, flush, startFlushTimer, stopFlushTimer };
