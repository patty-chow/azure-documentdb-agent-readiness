const express = require('express');
const bodyParser = require('body-parser');
const { connect } = require('./db');

const app = express();
app.use(bodyParser.json());

const Plan = require('./models/plan');
const Customer = require('./models/customer');
const Subscription = require('./models/subscription');
const ChargeEvent = require('./models/chargeEvent');

app.get('/plans', async (req, res) => {
  await connect();
  const plans = await Plan.find().lean();
  res.json(plans);
});

app.get('/customers', async (req, res) => {
  await connect();
  const customers = await Customer.find().lean();
  res.json(customers);
});

app.post('/charge', async (req, res) => {
  await connect();
  const { customerId, subscriptionId, amountCents, idempotencyKey } = req.body;
  if (!customerId || !subscriptionId || !amountCents || !idempotencyKey) {
    return res.status(400).json({ error: 'customerId, subscriptionId, amountCents and idempotencyKey required' });
  }

  // Idempotency pre-check
  const existing = await ChargeEvent.findOne({ idempotencyKey }).lean();
  if (existing) return res.json({ status: 'already_processed', charge: existing });

  const session = await ChargeEvent.startSession();
  try {
    session.startTransaction();

    const charge = await ChargeEvent.create([{ subscriptionId, customerId, amountCents, idempotencyKey }], { session });

    // Update subscription status to active as part of the charge
    await Subscription.findByIdAndUpdate(subscriptionId, { status: 'active', lastChargedAt: new Date() }, { session });

    await session.commitTransaction();
    session.endSession();
    res.json({ status: 'charged', charge: charge[0] });
  } catch (err) {
    await session.abortTransaction();
    session.endSession();
    // Duplicate key on idempotency -> return existing
    if (err && err.code === 11000) {
      const found = await ChargeEvent.findOne({ idempotencyKey }).lean();
      if (found) return res.json({ status: 'already_processed', charge: found });
    }
    console.error(err);
    res.status(500).json({ error: 'charge_failed', details: err.message });
  }
});

const port = process.env.PORT || 3000;
connect().then(() => {
  app.listen(port, () => console.log('Server listening on', port));
}).catch(err => {
  console.error('Failed to connect', err);
});
