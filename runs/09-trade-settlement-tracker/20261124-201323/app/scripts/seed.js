require('dotenv').config();
const { connect, mongoose } = require('../src/db');
const Trade = require('../src/models/trade');
const faker = require('faker');

const ASSET_CLASSES = ['Equity','FixedIncome','FX','Commodity'];
const COUNTERPARTIES = ['BankA','BankB','BrokerC','FundD'];

async function run() {
  await connect();

  // create indexes idempotently
  try {
    await Trade.collection.createIndex({ tradeId: 1 }, { unique: true });
    await Trade.collection.createIndex({ assetClass: 1, counterparty: 1, currentState: 1 });
    await Trade.collection.createIndex({ currentState: 1 });
  } catch (err) {
    console.warn('index creation warning', err.message);
  }

  const bulk = Trade.collection.initializeUnorderedBulkOp();
  const total = 200;
  for (let i = 0; i < total; i++) {
    const tradeId = `T-${String(i).padStart(6,'0')}`;
    const assetClass = ASSET_CLASSES[Math.floor(Math.random()*ASSET_CLASSES.length)];
    const counterparty = COUNTERPARTIES[Math.floor(Math.random()*COUNTERPARTIES.length)];
    const states = ['INIT','PENDING_SETTLEMENT','SETTLED','FAILED'];
    const currentState = states[Math.floor(Math.random()*states.length)];
    const doc = {
      tradeId,
      assetClass,
      counterparty,
      currentState,
      stateHistory: [{ from: null, to: currentState, at: new Date(), by: 'seed' }],
      metadata: { createdAt: new Date(), updatedAt: new Date() },
      version: 1
    };
    bulk.find({ tradeId }).upsert().replaceOne(doc);
  }
  try {
    if (bulk.length > 0) {
      const r = await bulk.execute();
      console.log('seeded', r.nUpserted + r.nModified);
    }
  } catch (err) {
    console.error('bulk error', err);
  }
}

if (require.main === module) {
  run().then(() => {
    console.log('done');
    process.exit(0);
  }).catch(err => {
    console.error(err);
    process.exit(1);
  });
}

module.exports = { run };
