const { connect, mongoose } = require('./db');
const axios = require('axios');

function evalComparison(lhs, op, rhs) {
  if (op === '>') return lhs > rhs;
  if (op === '<') return lhs < rhs;
  return false;
}

async function handleChange(change) {
  try {
    const doc = change.fullDocument;
    if (!doc) return;
    // We react only to price or position updates; for simplicity evaluate on any update
    const { userId, symbol, currentPrice, avgCost, shares } = doc;
    const pnl = (currentPrice - avgCost) * shares;

    // Find active alert rules for this user that either are global or match the symbol
    const AlertRule = mongoose.model('AlertRule');
    const rules = await AlertRule.find({ userId, active: true, $or: [ { scope: 'global' }, { symbol } ] });

    for (const r of rules) {
      let value = null;
      if (r.metric === 'price') value = currentPrice;
      else if (r.metric === 'pnl') value = pnl;
      else continue;

      if (evalComparison(value, r.comparison, r.threshold)) {
        // Fire webhook (single attempt sample policy)
        const payload = { userId, symbol, metric: r.metric, value, threshold: r.threshold, timestamp: new Date() };
        try {
          await axios.post(r.webhookUrl, payload, { timeout: 5000 });
          console.log(`Alert fired to ${r.webhookUrl} for user ${userId} ${r.metric}=${value}`);
        } catch (err) {
          console.error(`Failed to deliver webhook to ${r.webhookUrl}:`, err.message);
        }
      }
    }
  } catch (err) {
    console.error('Error handling change', err);
  }
}

let changeStream = null;

module.exports = {
  async start() {
    await connect();
    // ensure models are registered
    const PositionModel = mongoose.model('Position', require('./models/position'), 'positions');
    mongoose.model('AlertRule', require('./models/alertrule'), 'alertrules');

    // Open change stream with fullDocument lookup
    changeStream = PositionModel.watch([], { fullDocument: 'updateLookup' });
    changeStream.on('change', handleChange);
    changeStream.on('error', err => console.error('ChangeStream error', err));

    console.log('Alert watcher started (change stream)');
  },
  async stop() {
    if (changeStream) await changeStream.close();
  }
};
