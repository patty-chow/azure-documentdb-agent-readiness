// Pure function helpers for computing portfolio aggregates from an array of positions

function computePortfolioSummaryFromPositions(positions) {
  // positions: [{ symbol, shares, currentPrice, avgCost, sector }]
  const sectors = {};
  let totalPnl = 0;
  let totalMarketValue = 0;

  for (const p of positions) {
    const mv = (p.currentPrice || 0) * (p.shares || 0);
    const pnl = ((p.currentPrice || 0) - (p.avgCost || 0)) * (p.shares || 0);
    totalPnl += pnl;
    totalMarketValue += mv;
    const s = p.sector || 'Unknown';
    if (!sectors[s]) sectors[s] = { sector: s, marketValue: 0 };
    sectors[s].marketValue += mv;
  }

  const sectorArr = Object.values(sectors).map(s => ({
    sector: s.sector,
    marketValue: s.marketValue,
    percentage: totalMarketValue ? (s.marketValue / totalMarketValue) * 100 : 0
  }));

  return { totalPnl, totalMarketValue, sectors: sectorArr };
}

module.exports = { computePortfolioSummaryFromPositions };
