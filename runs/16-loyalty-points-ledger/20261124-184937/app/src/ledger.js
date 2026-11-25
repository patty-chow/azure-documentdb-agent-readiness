const { mongoose } = require('./db');
const { Event, Balance } = require('./models');

// Append an event and update balance atomically using a transaction.
// type = 'earn'|'redeem'
async function appendEventTransactional(accountId, type, amount, metadata = {}) {
  const session = await mongoose.startSession();
  session.startTransaction();
  try {
    // insert event
    const ev = await Event.create([{ accountId, type, amount, timestamp: new Date(), metadata }], { session });

    // read balance doc
    let bal = await Balance.findOne({ accountId }).session(session);
    if (!bal) {
      bal = await Balance.create([{ accountId, balance: 0, lifetimePoints: 0 }], { session });
      bal = bal[0];
    }
    // compute new balance
    const delta = type === 'earn' ? amount : -Math.abs(amount);
    const newBalance = bal.balance + delta;
    if (newBalance < 0) {
      throw new Error('Insufficient balance');
    }
    bal.balance = newBalance;
    if (type === 'earn') bal.lifetimePoints = (bal.lifetimePoints || 0) + amount;
    bal.updatedAt = new Date();
    await bal.save({ session });

    await session.commitTransaction();
    session.endSession();
    return ev[0];
  } catch (err) {
    await session.abortTransaction();
    session.endSession();
    throw err;
  }
}

module.exports = { appendEventTransactional };
