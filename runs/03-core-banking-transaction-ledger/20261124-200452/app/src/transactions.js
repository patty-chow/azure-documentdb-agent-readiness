const mongoose = require('mongoose');
const Transaction = require('./models/transaction');
const Account = require('./models/account');

/**
 * Post a transaction atomically: insert transaction document and update account balance snapshot.
 * Enforces idempotency via unique index on transactionRef. Caller must ensure inputs validated.
 */
async function postTransaction({ accountId, amount, type, transactionRef, metadata }) {
  if (!accountId || !transactionRef || !type || typeof amount !== 'number') {
    throw new Error('Missing required fields');
  }
  const signedAmount = type === 'debit' ? -Math.abs(amount) : Math.abs(amount);

  const session = await mongoose.startSession();
  try {
    let result;
    await session.withTransaction(async () => {
      // Insert transaction
      const tx = new Transaction({ transactionRef, accountId, amount: signedAmount, type, metadata });
      await tx.save({ session });

      // Update account balance snapshot
      const update = await Account.findOneAndUpdate(
        { accountId },
        { $inc: { balance: signedAmount } },
        { upsert: true, new: true, session }
      );
      result = { transaction: tx.toObject(), account: update.toObject() };
    });
    return result;
  } catch (err) {
    // Duplicate transactionRef -> idempotent: no change happened because transaction aborted
    if (err && err.code === 11000) {
      const existingAccount = await Account.findOne({ accountId }).lean();
      const existingTx = await Transaction.findOne({ transactionRef }).lean();
      const err2 = new Error('Duplicate transactionRef');
      err2.code = 11000;
      err2.existing = { tx: existingTx, account: existingAccount };
      throw err2;
    }
    throw err;
  } finally {
    session.endSession();
  }
}

module.exports = { postTransaction };
