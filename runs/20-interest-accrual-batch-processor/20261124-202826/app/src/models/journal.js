const mongoose = require('mongoose');

const JournalSchema = new mongoose.Schema({
  accountId: { type: mongoose.Schema.Types.ObjectId, required: true, index: true },
  runDate: { type: Date, required: true }, // date for which interest was accrued (day precision)
  amount: { type: Number, required: true },
  createdAt: { type: Date, default: Date.now }
}, { collection: 'accrual_journal', versionKey: false });

module.exports = mongoose.model('Journal', JournalSchema);
