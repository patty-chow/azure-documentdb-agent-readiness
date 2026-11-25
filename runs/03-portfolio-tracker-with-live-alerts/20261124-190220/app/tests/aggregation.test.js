const { computePortfolioSummaryFromPositions } = require('../src/aggregation');

test('compute portfolio summary basic', () => {
  const positions = [
    { symbol: 'A', shares: 10, avgCost: 10, currentPrice: 15, sector: 'X' },
    { symbol: 'B', shares: 5, avgCost: 20, currentPrice: 18, sector: 'Y' }
  ];
  const res = computePortfolioSummaryFromPositions(positions);
  // A: mv=150 pnl=50; B: mv=90 pnl=-10 => totalPnl=40 totalMV=240
  expect(res.totalPnl).toBeCloseTo(40);
  expect(res.totalMarketValue).toBeCloseTo(240);
  expect(res.sectors.length).toBe(2);
  const sx = res.sectors.find(s=>s.sector==='X');
  expect(sx.marketValue).toBeCloseTo(150);
});
