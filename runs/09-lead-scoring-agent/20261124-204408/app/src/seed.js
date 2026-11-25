const { getDb, getClient } = require('./db');

async function seed() {
  const db = await getDb();
  // Collections: leads, activities, companies, engagement_signals
  const leads = db.collection('leads');
  const activities = db.collection('activities');
  const companies = db.collection('companies');
  const signals = db.collection('engagement_signals');

  // Create indexes (id on _id is automatic)
  await activities.createIndex({ leadId: 1, timestamp: -1 });
  await signals.createIndex({ leadId: 1 });
  await companies.createIndex({ companyId: 1 }, { unique: true });
  await leads.createIndex({ leadId: 1 }, { unique: true });

  // Upsert sample companies
  const companyList = [
    { companyId: 'company-A', name: 'Alpha Corp', industry: 'Software', size: 250 },
    { companyId: 'company-B', name: 'Beta LLC', industry: 'Retail', size: 1200 }
  ];
  for (const c of companyList) {
    await companies.replaceOne({ companyId: c.companyId }, c, { upsert: true });
  }

  // Upsert sample leads
  const leadList = [
    { leadId: 'lead-1', name: 'Alice Adams', email: 'alice@example.com', companyId: 'company-A' },
    { leadId: 'lead-2', name: 'Bob Brown', email: 'bob@example.com', companyId: 'company-B' }
  ];
  for (const l of leadList) {
    await leads.replaceOne({ leadId: l.leadId }, { ...l, score: null, score_rationale: null }, { upsert: true });
  }

  // Activities: a few events per lead
  const now = Date.now();
  const activityDocs = [
    { _id: 'a1', leadId: 'lead-1', type: 'email_open', timestamp: new Date(now - 1000 * 60 * 60 * 24 * 3), details: 'Opened welcome email' },
    { _id: 'a2', leadId: 'lead-1', type: 'page_view', timestamp: new Date(now - 1000 * 60 * 60 * 24 * 2), details: 'Viewed pricing page' },
    { _id: 'a3', leadId: 'lead-2', type: 'email_click', timestamp: new Date(now - 1000 * 60 * 60 * 24 * 1), details: 'Clicked feature link' }
  ];
  for (const a of activityDocs) {
    await activities.replaceOne({ _id: a._id }, a, { upsert: true });
  }

  // Engagement signals
  const signalDocs = [
    { _id: 's1', leadId: 'lead-1', signal: 'marketing_score', value: 72 },
    { _id: 's2', leadId: 'lead-1', signal: 'time_on_site_minutes', value: 12 },
    { _id: 's3', leadId: 'lead-2', signal: 'marketing_score', value: 40 }
  ];
  for (const s of signalDocs) {
    await signals.replaceOne({ _id: s._id }, s, { upsert: true });
  }

  console.log('Seed data created/updated in database');
  // close client
  const client = await getClient();
  await client.close();
}

seed().catch(err => {
  console.error('Seed failed', err);
  process.exit(1);
});
