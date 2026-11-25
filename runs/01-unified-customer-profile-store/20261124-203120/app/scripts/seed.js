#!/usr/bin/env node
const { connect, mongoose } = require('../src/db');
const CustomerProfileSchema = require('../src/models/customerProfile');

async function seed() {
  await connect();
  const CustomerProfile = mongoose.model('CustomerProfile', CustomerProfileSchema);

  // Ensure indexes are created on the live cluster
  await CustomerProfile.syncIndexes();
  console.log('Indexes ensured.');

  // Small synthetic dataset — 30 customers with a few events each
  const sources = ['crm', 'ecommerce', 'support'];
  const customers = Array.from({ length: 30 }, (_, i) => `cust_${String(i+1).padStart(3,'0')}`);

  for (const cid of customers) {
    // Upsert a crm event
    await CustomerProfile.upsertFromEvent({ source: 'crm', customerId: cid, attributes: { name: `User ${cid}`, email: `${cid}@example.com` } });
    // Upsert ecommerce
    await CustomerProfile.upsertFromEvent({ source: 'ecommerce', customerId: cid, attributes: { loyaltyLevel: ['bronze','silver','gold'][Math.floor(Math.random()*3)], lastPurchaseAt: new Date() } });
    // Occasionally a support event
    if (Math.random() > 0.6) {
      await CustomerProfile.upsertFromEvent({ source: 'support', customerId: cid, attributes: { lastTicket: `TICKET-${Math.floor(Math.random()*1000)}`, openCount: Math.floor(Math.random()*5) } });
    }
  }

  console.log('Seeding complete.');
  await mongoose.disconnect();
}

seed().catch(err => {
  console.error('Seed failed', err);
  process.exit(1);
});
