const { Schema } = require('mongoose');
const tenantSafetyPlugin = require('./tenantSafetyPlugin');

const InventorySchema = new Schema({
  tenantId: { type: String, required: true, index: true },
  sku: { type: String, required: true },
  quantity: { type: Number, default: 0 },
  updatedAt: { type: Date, default: () => new Date() }
});

InventorySchema.plugin(tenantSafetyPlugin);
InventorySchema.index({ tenantId: 1, sku: 1 }, { unique: false });

module.exports = InventorySchema;
