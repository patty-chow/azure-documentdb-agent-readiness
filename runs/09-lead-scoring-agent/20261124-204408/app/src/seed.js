/*
Idempotent seed script: upserts sample leads, activities, companies, engagement_signals
and creates common indexes. Run: npm run seed
*/

require('dotenv').config();
const { getDb, getClient } = require('./db');

async function seed() {
  const db = await getDb();
  const leads = db.collection('leads');
  const activities = db.collection('activities');
  const companies = db.collection('companies');
  const signals = db.collection('engagement_signals');

  // Create indexes (basic, non-vector) — safe and portable
  await activities.createIndex({ leadId: 1, timestamp: -1 });
  await signals.createIndex({ leadId: 1 });
  // leads._id exists by default

  // Upsert sample companies
  await companies.updateOne({ companyId: 'company-1' }, {
    $set: {
      companyId: 'company-1',
      name: 'Contoso Widgets',
      industry: 'Manufacturing',
      employeeCount: 250
    }
  }, { upsert: true });

  // Upsert sample leads
  const sampleLeads = [
    { _id: 'lead-1', leadId: 'lead-1', name: 'Alice Example', companyId: 'company-1' },
    { _id: 'lead-2', leadId: 'lead-2', name: 'Bob Example', companyId: 'company-1' }
  ];
  for (const l of sampleLeads) {
    await leads.updateOne({ _id: l._id }, { $set: l }, { upsert: true });
  }

  // Upsert activities
  const now = new Date();
  await activities.updateOne({ _id: 'act-1' }, { $set: { _id: 'act-1', leadId: 'lead-1', type: 'email_open', timestamp: new Date(now - 1000 * 60 * 60 * 24) } }, { upsert: true });
  await activities.updateOne({ _id: 'act-2' }, { $set: { _id: 'act-2', leadId: 'lead-1', type: 'page_view', page: '/pricing', timestamp: new Date(now - 1000 * 60 * 60 * 2) } }, { upsert: true });
  await activities.updateOne({ _id: 'act-3' }, { $set: { _id: 'act-3', leadId: 'lead-2', type: 'email_click', timestamp: new Date(now - 1000 * 60 * 60 * 6) } }, { upsert: true });

  // Upsert engagement signals
  await signals.updateOne({ _id: 'sig-1' }, { $set: { _id: 'sig-1', leadId: 'lead-1', score: 0.8, notes: 'Opened pricing email and viewed pricing page' } }, { upsert: true });
  await signals.updateOne({ _id: 'sig-2' }, { $set: { _id: 'sig-2', leadId: 'lead-2', score: 0.3, notes: 'Clicked an email' } }, { upsert: true });

  console.log('Seed complete. Sample documents upserted into database:', db.databaseName);
  await getClient().close();
}

seed().catch(err => {
  console.error('Seed failed:', err);
  process.exit(1);
});
