const { Schema, model } = require('mongoose');

const SummarySchema = new Schema({
  _id: { type: String, default: 'network_summary' },
  counts: {
    online: { type: Number, default: 0 },
    offline: { type: Number, default: 0 },
    low_cash: { type: Number, default: 0 }
  },
  availability: { type: Number, default: 1.0 },
  lastUpdated: { type: Date, default: () => new Date() }
}, { _id: false });

module.exports = model('Summary', SummarySchema);
