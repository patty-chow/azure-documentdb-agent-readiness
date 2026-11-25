const { connect, mongoose } = require('../db');
const Trade = require('../models/trade');

let changeStream;

async function startChangeStream() {
  try {
    await connect();
    const pipeline = [ { $match: { 'fullDocument.currentState': 'FAILED' } } ];
    // Watch the trades collection for failed settlements
    changeStream = Trade.watch(pipeline, { fullDocument: 'updateLookup' });

    changeStream.on('change', (change) => {
      try {
        const doc = change.fullDocument;
        console.warn('Detected FAILED settlement for trade', doc.tradeId);
        // Trigger exception workflow — here we just log, but in production you'd
        // call an external service, enqueue a job, or open a ticket.
        handleFailedSettlement(doc).catch(console.error);
      } catch (err) {
        console.error('change event processing error', err);
      }
    });

    changeStream.on('error', (err) => {
      console.error('change stream error', err);
      // In production: implement resume token persistence and exponential backoff
    });

    console.log('change stream started');
  } catch (err) {
    console.error('failed to start change stream', err);
  }
}

async function handleFailedSettlement(doc) {
  // Minimal exception workflow: write an incident document or send alert
  console.log('Exception workflow: notify ops for trade', doc.tradeId, 'counterparty', doc.counterparty);
}

module.exports = startChangeStream;
