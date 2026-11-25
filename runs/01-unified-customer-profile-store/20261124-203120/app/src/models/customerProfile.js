const { Schema } = require('mongoose');

const CustomerProfileSchema = new Schema({
  customerId: { type: String, required: true, unique: true, index: true },
  crm: { type: Schema.Types.Mixed, default: {} },
  ecommerce: { type: Schema.Types.Mixed, default: {} },
  support: { type: Schema.Types.Mixed, default: {} },
  schemaVersion: { type: Number, default: 1 },
  lastUpdated: { type: Date, default: Date.now }
}, { collection: 'customer_profiles', timestamps: true });

// Static helper to upsert from an event while merging attributes into the subdocument using dot-paths
CustomerProfileSchema.statics.upsertFromEvent = async function (event) {
  const { source, customerId, attributes } = event;
  if (!['crm', 'ecommerce', 'support'].includes(source)) {
    throw new Error('unsupported source');
  }
  if (!customerId) throw new Error('customerId required');

  // Flatten attributes into dot notation under the source prefix
  const setOps = {};
  for (const [k, v] of Object.entries(attributes || {})) {
    setOps[`${source}.${k}`] = v;
  }
  setOps.lastUpdated = new Date();

  const res = await this.updateOne({ customerId }, { $set: setOps }, { upsert: true });
  return res;
};

module.exports = CustomerProfileSchema;
