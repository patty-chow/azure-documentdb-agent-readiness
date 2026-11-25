const { Schema } = require('mongoose');

const EventSchema = new Schema({
  accountId: { type: String, required: true, index: true },
  type: { type: String, required: true, enum: ['earn', 'redeem'] },
  amount: { type: Number, required: true },
  timestamp: { type: Date, required: true, default: () => new Date() },
  metadata: { type: Schema.Types.Mixed }
}, { collection: 'events' });

EventSchema.index({ accountId: 1, timestamp: -1 });

module.exports = EventSchema;
