const { mongoose } = require('../db');
const { Schema } = mongoose;

const ReturnSchema = new Schema({
  orderId: { type: String, required: true, index: true },
  status: { type: String, enum: ['approved','rejected','error'], required: true },
  refundAmount: { type: Number, default: 0 },
  currency: { type: String, default: 'USD' },
  reason: String,
  requester: String,
  policyResult: Schema.Types.Mixed,
  refundResult: Schema.Types.Mixed,
  commsResult: Schema.Types.Mixed,
  error: Schema.Types.Mixed,
  createdAt: { type: Date, default: () => new Date() },
  updatedAt: { type: Date, default: () => new Date() }
}, { collection: 'returns' });

ReturnSchema.index({ orderId: 1, createdAt: -1 });

module.exports = mongoose.models.Return || mongoose.model('Return', ReturnSchema);
