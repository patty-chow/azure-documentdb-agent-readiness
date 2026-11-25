require('dotenv').config();
const mongoose = require('mongoose');
const Collateral = require('../src/models/collateral');
const { classifyAsset } = require('../src/llm/classifier');

async function seed() {
  const uri = process.env.DOCUMENTDB_URI;
  const dbName = process.env.DB_NAME || 'sample_banking_06';
  if (!uri) {
    console.error('DOCUMENTDB_URI not set. Aborting seed.');
    process.exit(1);
  }
  await mongoose.connect(uri, { serverSelectionTimeoutMS: 5000, dbName });

  // Sample assets: upsert logic by assetId+version to be idempotent
  const samples = [
    { assetId: 'A-100', versions: [{ amount: 100000, currency: 'USD' }, { amount: 105000, currency: 'USD' }] , metadata: { category: 'residential_mortgage' }},
    { assetId: 'A-200', versions: [{ amount: 250000, currency: 'USD' }], metadata: { category: 'commercial_real_estate' }},
    { assetId: 'A-300', versions: [{ amount: 50000, currency: 'USD' }], metadata: { category: 'cash' }},
    { assetId: 'A-400', versions: [{ amount: 120000, currency: 'USD' }, { amount: 115000, currency: 'USD' }], metadata: { category: 'securities' }},
    { assetId: 'A-500', versions: [{ amount: 75000, currency: 'USD' }], metadata: { category: 'auto_loan' }}
  ];

  for (const s of samples) {
    // find current max version
    const arr = await Collateral.find({ assetId: s.assetId });
    const latest = (arr && arr.length) ? arr.sort((a,b) => b.version - a.version)[0] : null;
    let baseVersion = latest ? latest.version : 0;
    for (const v of s.versions) {
      baseVersion++;
      // check if this exact version exists (idempotency)
      const existsArr = await Collateral.find({ assetId: s.assetId, version: baseVersion });
      const exists = existsArr && existsArr[0];
      if (exists) continue;

      const doc = new Collateral({
        assetId: s.assetId,
        version: baseVersion,
        valuation: { amount: v.amount, currency: v.currency },
        metadata: s.metadata
      });
      // classify (may be disabled with DISABLE_LLM=true)
      const tags = await classifyAsset({ assetId: s.assetId, valuation: v, metadata: s.metadata });
      doc.llmTags = tags;
      await doc.save();
      console.log('Inserted', s.assetId, 'v', baseVersion);
    }
  }

  // Ensure indexes exist (mongoose created them via schema, but ensure)
  try {
    await Collateral.syncIndexes();
    console.log('Indexes synced on collateral_assets');
  } catch (e) {
    console.warn('Index sync failed:', e.message);
  }

  await mongoose.disconnect();
  console.log('Seed complete');
}

if (require.main === module) {
  seed().catch(err => {
    console.error('Seed failed:', err);
    process.exit(1);
  });
}
