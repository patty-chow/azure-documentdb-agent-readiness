const { Schema, model } = require('mongoose');

const HeartbeatSchema = new Schema({
  atmId: { type: String, required: true, index: true },
  timestamp: { type: Date, default: () => new Date(), index: true },
  status: { type: String, enum: ['online', 'offline', 'low_cash'], required: true, index: true },
  cashLevel: { type: Number },
  meta: { type: Schema.Types.Mixed }
});

HeartbeatSchema.index({ atmId: 1, timestamp: -1 });
HeartbeatSchema.index({ status: 1 });

module.exports = model('Heartbeat', HeartbeatSchema);
