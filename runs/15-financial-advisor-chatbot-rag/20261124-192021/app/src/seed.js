const { getDb } = require('./db');

// Deterministic embedding generator (seeded by doc id)
function seededRandom(seed) {
  // simple xorshift-ish
  let h = 2166136261 >>> 0;
  for (let i = 0; i < seed.length; i++) {
    h ^= seed.charCodeAt(i);
    h = Math.imul(h, 16777619);
  }
  return function () {
    h += 0x6D2B79F5;
    let t = Math.imul(h ^ (h >>> 15), 1 | h);
    t ^= t + Math.imul(t ^ (t >>> 7), 61 | t);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

function makeEmbedding(seed, dims = 1536) {
  const rnd = seededRandom(seed);
  const vec = new Array(dims).fill(0).map(() => rnd());
  // normalize for cosine
  const norm = Math.sqrt(vec.reduce((s, v) => s + v * v, 0));
  return vec.map((v) => v / norm);
}

async function seed() {
  const db = await getDb();
  const coll = db.collection('knowledge');

  // Create small set of ~20 financial knowledge articles
  const topics = [
    ['Bonds 101', 'An introduction to bonds, yields, durations, and credit risk.'],
    ['Municipal Bonds', 'How municipal bonds work, tax considerations, and typical issuers.'],
    ['Corporate Bonds', 'Investment grade vs high yield and common use-cases.'],
    ['Bond Duration', 'Explaining duration and sensitivity to rates.'],
    ['Diversification', 'Why diversification across asset classes reduces volatility.'],
    ['ETF Basics', 'How exchange-traded funds provide liquidity and diversification.'],
    ['Fixed Income Laddering', 'Laddering strategies for managing interest-rate risk.'],
    ['Yield Curve', 'What the yield curve indicates about the economy.'],
    ['Credit Ratings', 'How ratings agencies assess default risk.'],
    ['Inflation Impact', 'How inflation erodes fixed-income returns and hedges.'],
    ['Bond Funds vs Individual Bonds', 'Pros and cons of funds vs holding bonds directly.'],
    ['Taxable vs Tax-Exempt Bonds', 'When to prefer municipal tax-exempt bonds.'],
    ['Callable Bonds', 'Risks associated with callable features.'],
    ['Duration Hedging', 'Using derivatives and laddering to hedge duration.'],
    ['Liquidity Risk', 'Understanding secondary-market liquidity for bonds.'],
    ['Emerging Market Debt', 'Risks and returns of EM fixed income.'],
    ['Interest Rate Models', 'Basic intuition for interest rate movements.'],
    ['Credit Spread', 'How spreads compensate for credit risk.'],
    ['Bond Indices', 'Benchmarks used for fixed-income strategies.'],
    ['Risk-adjusted Return', 'Sharpe, Sortino and measures applied to bonds.']
  ];

  const docs = topics.map(([title, content], idx) => {
    const id = `doc-${idx + 1}`;
    const embedding = makeEmbedding(title + '|' + content);
    return {
      _id: id,
      title,
      content,
      embedding,
      metadata: { source: 'seed', id, date: new Date().toISOString(), model: 'local-seed', dims: 1536 }
    };
  });

  for (const doc of docs) {
    await coll.updateOne({ _id: doc._id }, { $set: doc }, { upsert: true });
  }

  console.log(`Seeded ${docs.length} documents into sample_fintech_15.knowledge`);
}

if (require.main === module) {
  seed().then(() => process.exit(0)).catch((err) => {
    console.error('Seed failed:', err);
    process.exit(1);
  });
} else {
  module.exports = seed;
}
