const mongoose = require('mongoose');

const AccountSchema = new mongoose.Schema({
  accountNumber: { type: String, required: true, unique: true },
  balance: { type: Number, required: true },
  interestRate: { type: Number, required: true }, // annual percentage, e.g. 1.5 means 1.5% APR
  status: { type: String, enum: ['active', 'closed'], default: 'active' },
  interestBearing: { type: Boolean, default: true },
  updatedAt: { type: Date, default: Date.now },
  schemaVersion: { type: Number, default: 1 }
}, { collection: 'accounts' });

// Indexes created by sample setup (see worker ensureIndexes)

module.exports = mongoose.model('Account', AccountSchema);
