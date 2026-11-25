const { Schema } = require('mongoose');

const InventorySchema = new Schema({
  sku: { type: String, required: true, unique: true, index: true },
  name: { type: String, required: true },
  price: { type: Number, required: true },
  stock: { type: Number, required: true, min: 0 },
  schemaVersion: { type: Number, default: 1 }
}, {
  optimisticConcurrency: true,
  timestamps: true
});

module.exports = InventorySchema;
