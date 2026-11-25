// One-shot script that performs a charge to demonstrate transaction + idempotency
const { connect } = require('../src/db');
const ChargeEvent = require('../src/models/chargeEvent');
const Subscription = require('../src/models/subscription');

async function run() {
  await connect();
  const sub = await Subscription.findOne().lean();
  if (!sub) {
    console.error('No subscription found. Run npm run seed first.');
    process.exit(1);
  }
  const idempotencyKey = 'test-charge-' + Date.now();
  console.log('Charging subscription', sub._id.toString(), 'with idempotencyKey', idempotencyKey);

  // First attempt should create the charge
  const res1 = await makeCharge(sub.customerId, sub._id, 500, idempotencyKey);
  console.log('First attempt result:', res1);

  // Second attempt with same idempotencyKey should return existing
  const res2 = await makeCharge(sub.customerId, sub._id, 500, idempotencyKey);
  console.log('Second attempt result (should be already_processed):', res2);

  process.exit(0);
}

async function makeCharge(customerId, subscriptionId, amountCents, idempotencyKey) {
  // Use the same logic as the API: check existing, then attempt transaction
  const existing = await ChargeEvent.findOne({ idempotencyKey }).lean();
  if (existing) return { status: 'already_processed', charge: existing };

  const session = await ChargeEvent.startSession();
  try {
    session.startTransaction();
    const [charge] = await ChargeEvent.create([{ subscriptionId, customerId, amountCents, idempotencyKey }], { session });
    await Subscription.findByIdAndUpdate(subscriptionId, { status: 'active', lastChargedAt: new Date() }, { session });
    await session.commitTransaction();
    session.endSession();
    return { status: 'charged', charge };
  } catch (err) {
    await session.abortTransaction();
    session.endSession();
    if (err && err.code === 11000) {
      const found = await ChargeEvent.findOne({ idempotencyKey }).lean();
      if (found) return { status: 'already_processed', charge: found };
    }
    return { status: 'error', error: err.message };
  }
}

run().catch(err => { console.error(err); process.exit(1); });
