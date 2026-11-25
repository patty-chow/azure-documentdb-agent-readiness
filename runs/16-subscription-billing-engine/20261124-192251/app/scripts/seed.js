// Idempotent seed script: upserts plans, customers, subscriptions and entitlements
const { connect } = require('../src/db');
const Plan = require('../src/models/plan');
const Customer = require('../src/models/customer');
const Subscription = require('../src/models/subscription');
const Entitlement = require('../src/models/entitlement');

async function run() {
  await connect();
  console.log('Seeding sample data...');

  const plans = [
    { planId: 'basic-monthly', name: 'Basic Monthly', priceCents: 500, interval: 'monthly' },
    { planId: 'pro-monthly', name: 'Pro Monthly', priceCents: 1500, interval: 'monthly' },
    { planId: 'pro-yearly', name: 'Pro Yearly', priceCents: 15000, interval: 'yearly' }
  ];

  for (const p of plans) {
    await Plan.findOneAndUpdate({ planId: p.planId }, p, { upsert: true });
  }

  const customersData = [
    { email: 'alice@example.com', name: 'Alice' },
    { email: 'bob@example.com', name: 'Bob' },
    { email: 'carol@example.com', name: 'Carol' }
  ];

  const customers = [];
  for (const c of customersData) {
    const doc = await Customer.findOneAndUpdate({ email: c.email }, c, { upsert: true, new: true });
    customers.push(doc);
  }

  // Create a subscription for the first customer
  const customer0 = customers[0];
  const sub = await Subscription.findOneAndUpdate(
    { customerId: customer0._id },
    { customerId: customer0._id, planId: 'basic-monthly', status: 'trialing', startedAt: new Date(), trialExpiresAt: new Date(Date.now() + 7*24*60*60*1000) },
    { upsert: true, new: true }
  );

  // Create a trial entitlement that will expire (TTL index manages removal)
  await Entitlement.findOneAndUpdate({ customerId: customer0._id, type: 'trial' }, { customerId: customer0._id, type: 'trial', expiresAt: new Date(Date.now() + 7*24*60*60*1000) }, { upsert: true });

  console.log('Seed complete. Customer id:', customer0._id.toString(), 'subscription id:', sub._id.toString());
  process.exit(0);
}

run().catch(err => { console.error(err); process.exit(1); });
