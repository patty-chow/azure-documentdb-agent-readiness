const { getDb } = require('./db');
require('dotenv').config();

const SANDBOX = (process.env.SANDBOX_SEND || 'true') === 'true';

async function sendMessage(outreach) {
  // outreach: { eventId, customerId, channel, message }
  // In sandbox mode we do not actually send. We record the attempt in outreach_logs.
  const db = await getDb();
  const logs = db.collection('outreach_logs');
  const record = {
    logId: outreach.logId,
    eventId: outreach.eventId,
    customerId: outreach.customerId,
    channel: outreach.channel,
    message: outreach.message,
    status: SANDBOX ? 'mocked' : 'sent',
    sentAt: new Date(),
  };
  await logs.insertOne(record);
  if (SANDBOX) {
    console.log('[sendAgent] sandbox send:', record);
    return { ok: true, sandbox: true };
  }
  // TODO: integrate with real provider
  console.log('[sendAgent] would send via real provider:', record);
  return { ok: true, sandbox: false };
}

module.exports = { sendMessage };
