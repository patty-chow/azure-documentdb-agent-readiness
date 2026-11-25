const { Schema, model } = require('mongoose');

const LineItem = new Schema({
  description: String,
  quantity: Number,
  unitPrice: Number,
  extAmount: Number
}, { _id: false });

const POSchema = new Schema({
  poNumber: { type: String, required: true, index: true },
  vendorName: String,
  totalAmount: Number,
  lineItems: [LineItem]
}, { timestamps: true });

module.exports = model('PurchaseOrder', POSchema);
