const { mongoose } = require('../db');
const Schema = mongoose.Schema;

const ChargeEventSchema = new Schema({
  subscriptionId: { type: Schema.Types.ObjectId, ref: 'Subscription', required: true, index: true },
  customerId: { type: Schema.Types.ObjectId, ref: 'Customer', required: true, index: true },
  amountCents: { type: Number, required: true },
  currency: { type: String, default: 'USD' },
  idempotencyKey: { type: String, required: true },
  metadata: { type: Schema.Types.Mixed }
}, { timestamps: true });

// We will create a unique index on idempotencyKey with scripts/create_indexes.js

module.exports = mongoose.model('ChargeEvent', ChargeEventSchema);
