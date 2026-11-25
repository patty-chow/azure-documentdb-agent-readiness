import mongoose from 'mongoose';

const LineItem = new mongoose.Schema({
  description: String,
  quantity: Number,
  unitPrice: Number
}, {_id: false});

const PurchaseOrderSchema = new mongoose.Schema({
  poNumber: { type: String, required: true, index: true },
  vendorName: { type: String, required: true, index: true },
  totalAmount: { type: Number, required: true, index: true },
  lineItems: [LineItem],
  createdAt: { type: Date, default: () => new Date() }
});

export default mongoose.models.PurchaseOrder || mongoose.model('PurchaseOrder', PurchaseOrderSchema);
