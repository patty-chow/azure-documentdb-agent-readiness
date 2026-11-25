import { connect, disconnect } from './db.js';
import PurchaseOrder from './models/purchaseOrder.js';
import Invoice from './models/invoice.js';

async function seed() {
  await connect();

  console.log('Seeding sample_fintech_12...');

  // Idempotent: only insert if collections are empty
  const poCount = await PurchaseOrder.countDocuments();
  const invCount = await Invoice.countDocuments();

  if (poCount === 0) {
    console.log('Inserting sample purchase orders...');
    await PurchaseOrder.insertMany([
      { poNumber: 'PO-1001', vendorName: 'Acme Corporation', totalAmount: 1000, lineItems: [{description:'Widgets', quantity:10, unitPrice:100}] },
      { poNumber: 'PO-1002', vendorName: 'Global Industries', totalAmount: 2500, lineItems: [{description:'Thingamajigs', quantity:50, unitPrice:50}] },
      { poNumber: 'PO-1003', vendorName: 'Acme Corp', totalAmount: 1500, lineItems: [{description:'Gadgets', quantity:15, unitPrice:100}] },
      { poNumber: 'PO-1004', vendorName: 'Sprocket LLC', totalAmount: 980, lineItems: [{description:'Sprockets', quantity:49, unitPrice:20}] }
    ]);
  } else {
    console.log('PurchaseOrders already present, skipping insert. Count=', poCount);
  }

  if (invCount === 0) {
    console.log('Inserting sample invoices...');
    await Invoice.insertMany([
      { invoiceNumber: 'INV-9001', vendorName: 'Acme Corporation', totalAmount: 1000, invoiceDate: new Date('2026-01-12') },
      { invoiceNumber: 'INV-9002', vendorName: 'acme corp', totalAmount: 1500, invoiceDate: new Date('2026-01-15') },
      { invoiceNumber: 'INV-9003', vendorName: 'Global Industries', totalAmount: 2490, invoiceDate: new Date('2026-02-01') },
      { invoiceNumber: 'INV-9004', vendorName: 'Unknown Vendor', totalAmount: 500, invoiceDate: new Date('2026-02-07') }
    ]);
  } else {
    console.log('Invoices already present, skipping insert. Count=', invCount);
  }

  console.log('Seed complete.');
  await disconnect();
}

seed().catch(err => { console.error(err); process.exit(1); });
