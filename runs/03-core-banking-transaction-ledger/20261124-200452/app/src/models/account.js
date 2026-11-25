const mongoose = require('mongoose');

const AccountSchema = new mongoose.Schema({
  accountId: { type: String, required: true, unique: true, index: true },
  name: { type: String },
  balance: { type: Number, required: true, default: 0 },
  currency: { type: String, default: 'USD' }
}, { timestamps: true });

// Prevent accidental updates to balance outside controlled transactions is an app policy; not enforced at DB level

module.exports = mongoose.model('Account', AccountSchema);
