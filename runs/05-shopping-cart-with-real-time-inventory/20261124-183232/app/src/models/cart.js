const { Schema } = require('mongoose');

const ItemSchema = new Schema({
  productId: { type: Schema.Types.ObjectId, required: true },
  sku: { type: String, required: true },
  name: { type: String, required: true },
  price: { type: Number, required: true },
  quantity: { type: Number, required: true, min: 1 }
}, { _id: false });

const CartSchema = new Schema({
  userId: { type: String, required: true, index: true },
  items: { type: [ItemSchema], default: [] },
  schemaVersion: { type: Number, default: 1 }
}, {
  optimisticConcurrency: true,
  timestamps: true
});

module.exports = CartSchema;
