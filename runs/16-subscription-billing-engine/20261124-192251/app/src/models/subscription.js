const { mongoose } = require('../db');
const Schema = mongoose.Schema;

const SubscriptionSchema = new Schema({
  customerId: { type: Schema.Types.ObjectId, ref: 'Customer', required: true, index: true },
  planId: { type: String, required: true },
  status: { type: String, enum: ['active','past_due','cancelled','trialing'], default: 'trialing' },
  startedAt: { type: Date, default: () => new Date() },
  trialExpiresAt: { type: Date }
}, { timestamps: true });

module.exports = mongoose.model('Subscription', SubscriptionSchema);
