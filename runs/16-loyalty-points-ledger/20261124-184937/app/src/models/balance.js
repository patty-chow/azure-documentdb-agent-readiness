const { Schema, model } = require('mongoose');

const BalanceSchema = new Schema({
  accountId: { type: String, required: true, unique: true },
  balance: { type: Number, required: true, default: 0 },
  lifetimePoints: { type: Number, required: true, default: 0 },
  updatedAt: { type: Date, default: () => new Date() }
}, { collection: 'balances' });

BalanceSchema.index({ accountId: 1 }, { unique: true });

module.exports = model('Balance', BalanceSchema);
