const dbModule = require('../src/db');
const { createModel } = require('../src/models/customer');

async function run() {
  const db = await dbModule.connect();
  const Customer = createModel(db);
  const docs = await Customer.find({}).lean().limit(100);
  console.log('Customers in DB:');
  console.log(JSON.stringify(docs, null, 2));
  process.exit(0);
}

run().catch(err => {
  console.error('Verify failed:', err);
  process.exit(1);
});
