const { Schema } = require('mongoose');

const AlertRuleSchema = new Schema({
  userId: { type: String, required: true, index: true },
  scope: { type: String, enum: ['symbol', 'global'], default: 'symbol' },
  symbol: { type: String },
  metric: { type: String, enum: ['price', 'pnl'], required: true },
  comparison: { type: String, enum: ['>', '<'], required: true },
  threshold: { type: Number, required: true },
  webhookUrl: { type: String, required: true },
  active: { type: Boolean, default: true },
  createdAt: { type: Date, default: Date.now }
});

// Useful index patterns
AlertRuleSchema.index({ userId: 1 });
AlertRuleSchema.index({ userId: 1, active: 1 });

module.exports = AlertRuleSchema;
