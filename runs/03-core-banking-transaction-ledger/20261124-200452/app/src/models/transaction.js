const mongoose = require('mongoose');

const TransactionSchema = new mongoose.Schema({
  transactionRef: { type: String, required: true, unique: true },
  accountId: { type: String, required: true, index: true },
  amount: { type: Number, required: true },
  type: { type: String, enum: ['debit', 'credit'], required: true },
  metadata: { type: mongoose.Schema.Types.Mixed }
}, { timestamps: { createdAt: 'createdAt', updatedAt: false } });

// Indexes: unique transactionRef and compound for recent-account activity
TransactionSchema.index({ transactionRef: 1 }, { unique: true });
TransactionSchema.index({ accountId: 1, createdAt: -1 });

module.exports = mongoose.model('Transaction', TransactionSchema);
