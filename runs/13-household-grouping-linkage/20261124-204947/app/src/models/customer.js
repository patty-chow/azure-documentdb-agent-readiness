const { Schema, model } = require('mongoose');

const ProductSchema = new Schema({
  productId: String,
  name: String,
  quantity: { type: Number, default: 1 }
}, { _id: false });

const CustomerSchema = new Schema({
  givenName: String,
  surname: String,
  phone: String,
  address: String,
  normalizedAddress: String,
  clv: { type: Number, default: 0 },
  products: [ProductSchema],
  createdAt: { type: Date, default: () => new Date() }
});

CustomerSchema.index({ normalizedAddress: 1, phone: 1, surname: 1 });
CustomerSchema.index({ clv: 1 });
CustomerSchema.index({ 'products.productId': 1 });

module.exports = model('Customer', CustomerSchema);
