const express = require('express');
const { connect, mongoose } = require('./db');
const PositionSchema = require('./models/position');
const AlertRuleSchema = require('./models/alertrule');

const app = express();
app.use(express.json());

async function main() {
  await connect();
  const Position = mongoose.model('Position', PositionSchema, 'positions');
  const AlertRule = mongoose.model('AlertRule', AlertRuleSchema, 'alertrules');

  // simple portfolio summary endpoint
  app.get('/portfolio/:userId/summary', async (req, res) => {
    const userId = req.params.userId;
    try {
      const agg = await Position.aggregate([
        { $match: { userId } },
        { $project: {
            marketValue: { $multiply: ['$currentPrice', '$shares'] },
            pnl: { $multiply: [{ $subtract: ['$currentPrice', '$avgCost'] }, '$shares'] },
            sector: '$sector'
        } },
        { $group: {
            _id: '$sector',
            marketValue: { $sum: '$marketValue' },
            pnl: { $sum: '$pnl' }
        } },
        { $group: {
            _id: null,
            totalPnl: { $sum: '$pnl' },
            sectors: { $push: { sector: '$_id', marketValue: '$marketValue' } },
            totalMarketValue: { $sum: '$marketValue' }
        } },
        { $project: { _id: 0, totalPnl: 1, sectors: 1, totalMarketValue: 1 } }
      ]).exec();

      const result = agg[0] || { totalPnl: 0, sectors: [], totalMarketValue: 0 };
      // compute percentages
      result.sectors = result.sectors.map(s => ({
        sector: s.sector,
        marketValue: s.marketValue,
        percentage: result.totalMarketValue ? (s.marketValue / result.totalMarketValue) : 0
      }));

      res.json(result);
    } catch (err) {
      console.error('agg err', err);
      res.status(500).json({ error: String(err) });
    }
  });

  const port = process.env.PORT || 3000;
  app.listen(port, () => console.log('Server listening on', port));

  // start change stream worker in background (non-blocking)
  const worker = require('./worker/watch');
  worker.start(Position, AlertRule);
}

main().catch(err => {
  console.error(err);
  process.exit(1);
});
