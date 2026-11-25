const { mongoose } = require('../db');
const Schema = mongoose.Schema;

const EntitlementSchema = new Schema({
  customerId: { type: Schema.Types.ObjectId, ref: 'Customer', required: true, index: true },
  type: { type: String, enum: ['trial','promo'], default: 'trial' },
  expiresAt: { type: Date, required: true }
}, { timestamps: true });

// TTL index on expiresAt will be created by scripts/create_indexes.js

module.exports = mongoose.model('Entitlement', EntitlementSchema);
