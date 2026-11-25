const { getDb } = require('./db');

async function getCustomerJourney(customerId) {
  if (!customerId) throw new Error('customerId is required');
  const db = await getDb();
  const coll = db.collection('touchpoints');

  // Timeline: chronological events
  const timeline = await coll.find({ customerId }).sort({ timestamp: 1 }).toArray();

  // Group by channel while preserving order
  const byChannel = {};
  for (const ev of timeline) {
    const ch = ev.channel || 'unknown';
    if (!byChannel[ch]) byChannel[ch] = [];
    byChannel[ch].push(ev);
  }

  return { customerId, timeline, byChannel };
}

module.exports = { getCustomerJourney };
