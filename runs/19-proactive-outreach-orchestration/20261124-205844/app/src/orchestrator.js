const { v4: uuidv4 } = require('uuid');
const { getDb } = require('./db');
const copyAgent = require('./copyAgent');
const sendAgent = require('./sendAgent');

async function processEvent(event) {
  const db = await getDb();
  const customers = db.collection('customers');
  const cust = await customers.findOne({ customerId: event.customerId });
  if (!cust) {
    console.warn('No customer found for event', event);
    return;
  }
  // call copy agent
  const message = await copyAgent.generateMessage(cust, event);
  const outreach = {
    logId: uuidv4(),
    eventId: event.eventId,
    customerId: event.customerId,
    channel: cust.preferred_channel || 'email',
    message,
  };
  const result = await sendAgent.sendMessage(outreach);
  return { outreach, result };
}

module.exports = { processEvent };
