const { getDb } = require('./db');

const samples = [
  {
    applicationId: 'app-001',
    name: 'Alice Smith',
    income: 120000,
    liabilities: 15000,
    requested_amount: 300000,
    property_value: 420000,
    credit_score: 720,
    employment: [{ employer: 'Acme Corp', years: 5 }],
    documents: ['id', 'paystubs']
  },
  {
    applicationId: 'app-002',
    name: 'Bob Jones',
    income: 60000,
    liabilities: 10000,
    requested_amount: 350000,
    property_value: 360000,
    credit_score: 640,
    employment: [],
    documents: []
  },
  {
    applicationId: 'app-003',
    name: 'Carol Nguyen',
    income: 90000,
    liabilities: 20000,
    requested_amount: 200000,
    property_value: 250000,
    credit_score: 680,
    employment: [{ employer: 'SmallCo', years: 2 }],
    documents: ['id']
  }
];

async function seed() {
  console.log('Seeding sample applications...');
  const db = await getDb();
  const apps = db.collection('applications');

  for (const s of samples) {
    await apps.updateOne({ applicationId: s.applicationId }, { $set: s }, { upsert: true });
  }

  // Create indexes useful for the sample
  await apps.createIndex({ applicationId: 1 }, { unique: true });
  await apps.createIndex({ name: 'text' });
  await apps.createIndex({ credit_score: 1 });

  console.log('Seed complete. Inserted/updated sample applications.');
}

if (require.main === module) {
  seed().then(() => process.exit(0)).catch(err => { console.error(err); process.exit(1); });
}

module.exports = { seed };
