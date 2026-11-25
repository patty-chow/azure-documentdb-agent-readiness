const { mongoose } = require('../db');
const { Schema } = mongoose;

const ItemSchema = new Schema({
  sku: String,
  name: String,
  qty: Number,
  price: Number
}, { _id: false });

const OrderSchema = new Schema({
  orderId: { type: String, required: true, unique: true },
  customerId: String,
  total: Number,
  currency: { type: String, default: 'USD' },
  items: [ItemSchema],
  purchaseDate: Date
}, { collection: 'orders' });

module.exports = mongoose.models.Order || mongoose.model('Order', OrderSchema);
