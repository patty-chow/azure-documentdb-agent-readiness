/* One-shot aggregation runner for manual verification */
const { connect, mongoose } = require('../src/db');
const PositionSchema = require('../src/models/position');

async function run(userId = 'user1') {
  await connect();
  const Position = mongoose.model('Position', PositionSchema, 'positions');

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
    { $project: { _id: 0, totalMarketValue: 1, totalPnl: 1, sectors: 1 } }
  ];

  const rows = await Position.aggregate(pipeline).exec();
  const result = rows[0] || { totalMarketValue: 0, totalPnl: 0, sectors: [] };
  const sectorsWithPct = result.sectors.map(s => ({ sector: s.sector || 'Unknown', marketValue: s.marketValue || 0, percentage: result.totalMarketValue ? (s.marketValue / result.totalMarketValue) * 100 : 0 }));

  console.log(JSON.stringify({ totalPnl: result.totalPnl || 0, totalMarketValue: result.totalMarketValue || 0, sectors: sectorsWithPct }, null, 2));
  process.exit(0);
}

const userId = process.argv[2] || 'user1';
run(userId).catch(err => { console.error(err); process.exit(1); });
