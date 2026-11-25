const express = require('express');
const { connect, mongoose } = require('./db');
const PositionSchema = require('./models/position');

const app = express();
app.use(express.json());

const Position = mongoose.model('Position', PositionSchema, 'positions');

// GET /portfolio/:userId/summary — aggregation using MongoDB pipeline
app.get('/portfolio/:userId/summary', async (req, res) => {
  const userId = req.params.userId;
  try {
    await connect();

    // Pipeline: compute per-position marketValue and pnl, then sum and group by sector
    const pipeline = [
      { $match: { userId } },
      { $project: {
        symbol: 1,
        sector: 1,
        shares: 1,
        currentPrice: 1,
        avgCost: 1,
        marketValue: { $multiply: [ "$currentPrice", "$shares" ] },
        pnl: { $multiply: [ { $subtract: [ "$currentPrice", "$avgCost" ] }, "$shares" ] }
      }},
      { $group: {
        _id: "$sector",
        sectorMarketValue: { $sum: "$marketValue" },
        sectorPnl: { $sum: "$pnl" }
      }},
      { $group: {
        _id: null,
        totalMarketValue: { $sum: "$sectorMarketValue" },
        totalPnl: { $sum: "$sectorPnl" },
        sectors: { $push: { sector: "$_id", marketValue: "$sectorMarketValue" } }
      }},
      { $project: {
        _id: 0,
        totalMarketValue: 1,
        totalPnl: 1,
        sectors: 1
      }}
    ];

    const rows = await Position.aggregate(pipeline).exec();
    const result = rows[0] || { totalMarketValue: 0, totalPnl: 0, sectors: [] };
    // compute percentage per sector
    const sectorsWithPct = result.sectors.map(s => ({
      sector: s.sector || 'Unknown',
      marketValue: s.marketValue || 0,
      percentage: result.totalMarketValue ? (s.marketValue / result.totalMarketValue) * 100 : 0
    }));

    res.json({ totalPnl: result.totalPnl || 0, totalMarketValue: result.totalMarketValue || 0, sectors: sectorsWithPct });
  } catch (err) {
    console.error(err);
    res.status(500).json({ error: err.message });
  }
});

module.exports = app;
