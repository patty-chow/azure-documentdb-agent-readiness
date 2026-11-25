const { Schema, model } = require('mongoose');

const AtmStatusSchema = new Schema({
  atmId: { type: String, required: true, unique: true },
  status: { type: String, enum: ['online', 'offline', 'low_cash'], required: true },
  lastSeen: { type: Date, default: () => new Date() }
});

AtmStatusSchema.index({ atmId: 1 }, { unique: true });

module.exports = model('AtmStatus', AtmStatusSchema);
