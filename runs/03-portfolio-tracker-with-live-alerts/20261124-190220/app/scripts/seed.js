/* Idempotent seed script — upserts sample positions and alert rules */
const { connect, mongoose } = require('../src/db');
const PositionSchema = require('../src/models/position');
const AlertRuleSchema = require('../src/models/alertrule');

async function seed() {
  await connect();
  const Position = mongoose.model('Position', PositionSchema, 'positions');
  const AlertRule = mongoose.model('AlertRule', AlertRuleSchema, 'alertrules');

  const positions = [
    { userId: 'user1', symbol: 'AAPL', shares: 10, avgCost: 140, currentPrice: 170, sector: 'Technology' },
    { userId: 'user1', symbol: 'MSFT', shares: 5, avgCost: 250, currentPrice: 300, sector: 'Technology' },
    { userId: 'user1', symbol: 'JNJ', shares: 20, avgCost: 150, currentPrice: 155, sector: 'Healthcare' },
    { userId: 'user2', symbol: 'TSLA', shares: 2, avgCost: 600, currentPrice: 700, sector: 'Automotive' }
  ];

  for (const p of positions) {
    await Position.updateOne({ userId: p.userId, symbol: p.symbol }, { $set: p }, { upsert: true });
  }

  const rules = [
    { userId: 'user1', scope: 'symbol', symbol: 'AAPL', metric: 'price', comparison: '>', threshold: 160, webhookUrl: 'https://webhook.site/your-url-1', active: true },
    { userId: 'user1', scope: 'global', metric: 'pnl', comparison: '<', threshold: -100, webhookUrl: 'https://webhook.site/your-url-2', active: true }
  ];

  for (const r of rules) {
    // unique by userId + scope + symbol + metric + comparison + threshold
    const filter = { userId: r.userId, scope: r.scope, metric: r.metric, comparison: r.comparison, threshold: r.threshold, webhookUrl: r.webhookUrl };
    await AlertRule.updateOne(filter, { $set: r }, { upsert: true });
  }

  console.log('Seed complete');
  process.exit(0);
}

seed().catch(err => { console.error(err); process.exit(1); });
