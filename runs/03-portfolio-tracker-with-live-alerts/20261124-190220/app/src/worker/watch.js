const fetch = require('node-fetch');

// Simple alert evaluator and webhook sender

function shouldFire(rule, position) {
  let metricValue;
  if (rule.metric === 'price') metricValue = position.currentPrice;
  else if (rule.metric === 'pnl') metricValue = (position.currentPrice - position.avgCost) * position.shares;
  else return false;

  if (rule.comparison === '>') return metricValue > rule.threshold;
  if (rule.comparison === '<') return metricValue < rule.threshold;
  return false;
}

async function sendWebhook(url, payload) {
  // simple one-retry policy
  try {
    const res = await fetch(url, { method: 'POST', body: JSON.stringify(payload), headers: { 'content-type': 'application/json' }, timeout: 5000 });
    return { ok: res.ok, status: res.status };
  } catch (err) {
    // retry once after short backoff
    await new Promise(r => setTimeout(r, 500));
    try {
      const res2 = await fetch(url, { method: 'POST', body: JSON.stringify(payload), headers: { 'content-type': 'application/json' }, timeout: 5000 });
      return { ok: res2.ok, status: res2.status };
    } catch (err2) {
      return { ok: false, error: String(err2) };
    }
  }
}

function start(Position, AlertRule) {
  console.log('Starting positions change stream');
  const pipeline = [
    { $match: { 'operationType': { $in: ['insert', 'update', 'replace'] } } }
  ];
  const changeStream = Position.watch(pipeline, { fullDocument: 'updateLookup' });
  changeStream.on('change', async (change) => {
    try {
      const doc = change.fullDocument;
      if (!doc) return;
      console.log('Position change for', doc.userId, doc.symbol, 'price', doc.currentPrice);

      // find candidate rules: user's rules plus global rules
      const rules = await AlertRule.find({ userId: doc.userId, active: true }).or([{ scope: 'global' }, { scope: 'symbol', symbol: doc.symbol }]).exec();
      for (const rule of rules) {
        if (shouldFire(rule, doc)) {
          console.log('Rule fired for', rule._id, '-> webhook', rule.webhookUrl);
          const payload = { ruleId: rule._id, userId: doc.userId, symbol: doc.symbol, metric: rule.metric, currentPrice: doc.currentPrice };
          const r = await sendWebhook(rule.webhookUrl, payload);
          console.log('Webhook result', r);
        }
      }
    } catch (err) {
      console.error('change handling error', err);
    }
  });
  changeStream.on('error', (err) => console.error('changeStream error', err));
}

module.exports = { start };
