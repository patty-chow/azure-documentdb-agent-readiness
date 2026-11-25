import mongoose from 'mongoose';

const LineItem = new mongoose.Schema({
  description: String,
  quantity: Number,
  unitPrice: Number
}, {_id: false});

const InvoiceSchema = new mongoose.Schema({
  invoiceNumber: { type: String, required: true, index: true },
  vendorName: { type: String, required: true, index: true },
  totalAmount: { type: Number, required: true, index: true },
  invoiceDate: Date,
  lineItems: [LineItem],
  status: { type: String, default: 'unmatched', index: true },
  referencedPoNumber: String,
  matchedPoId: { type: mongoose.Schema.Types.ObjectId, ref: 'PurchaseOrder' },
  matchScore: Number,
  matchDetails: Object,
  matchedAt: Date,
  createdAt: { type: Date, default: () => new Date() }
});

export default mongoose.models.Invoice || mongoose.model('Invoice', InvoiceSchema);
