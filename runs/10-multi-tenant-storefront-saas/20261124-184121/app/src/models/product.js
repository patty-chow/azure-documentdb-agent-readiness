const { Schema } = require('mongoose');
const tenantSafetyPlugin = require('./tenantSafetyPlugin');

const ProductSchema = new Schema({
  tenantId: { type: String, required: true, index: true },
  sku: { type: String, required: true },
  name: { type: String, required: true },
  description: String,
  price: Number,
  createdAt: { type: Date, default: () => new Date() }
});

ProductSchema.plugin(tenantSafetyPlugin);
// compound index: (tenantId, sku) unique per tenant
ProductSchema.index({ tenantId: 1, sku: 1 }, { unique: true });

module.exports = ProductSchema;
