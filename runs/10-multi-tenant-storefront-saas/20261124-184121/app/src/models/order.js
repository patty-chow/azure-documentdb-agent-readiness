const { Schema } = require('mongoose');
const tenantSafetyPlugin = require('./tenantSafetyPlugin');

const OrderSchema = new Schema({
  tenantId: { type: String, required: true, index: true },
  orderNumber: { type: String, required: true },
  items: [
    {
      sku: String,
      qty: Number,
      price: Number
    }
  ],
  total: Number,
  createdAt: { type: Date, default: () => new Date() }
});

OrderSchema.plugin(tenantSafetyPlugin);
OrderSchema.index({ tenantId: 1, createdAt: -1 });

module.exports = OrderSchema;
