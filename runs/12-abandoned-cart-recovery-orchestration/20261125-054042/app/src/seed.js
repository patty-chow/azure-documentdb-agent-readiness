require('dotenv').config();
const { getDb } = require('./db');

async function seed() {
  const db = await getDb();
  const customers = db.collection('customers');
  const carts = db.collection('carts');

  // idempotent marker
  const marker = { sample: 'abandoned-cart-sample-12' };

  // upsert a few customers
  const sampleCustomers = [
    { _id: 'cust-1', name: 'Alice', email: 'alice@example.com', phone: '+15550001', preferredChannel: 'email' },
    { _id: 'cust-2', name: 'Bob', email: 'bob@example.com', phone: '+15550002', preferredChannel: 'sms' },
    { _id: 'cust-3', name: 'Carlos', email: 'carlos@example.com', phone: '+15550003', preferredChannel: 'email' }
  ];

  for (const c of sampleCustomers) {
    await customers.updateOne({ _id: c._id }, { $set: { ...c, ...marker } }, { upsert: true });
  }

  // create carts: some old (>2h) and some recent
  const now = new Date();
  const old = new Date(now.getTime() - 1000 * 60 * 60 * 3); // 3 hours ago
  const recent = new Date(now.getTime() - 1000 * 60 * 30); // 30 minutes ago

  const sampleCarts = [
    { _id: 'cart-1', customerId: 'cust-1', items: [{ name: 'Red T-shirt', qty: 2 }], lastUpdated: old, status: 'abandoned', ...marker },
    { _id: 'cart-2', customerId: 'cust-2', items: [{ name: 'Blue Jeans', qty: 1 }], lastUpdated: old, status: 'abandoned', ...marker },
    { _id: 'cart-3', customerId: 'cust-3', items: [{ name: 'Sneakers', qty: 1 }], lastUpdated: recent, status: 'active', ...marker }
  ];

  for (const cart of sampleCarts) {
    await carts.updateOne({ _id: cart._id }, { $set: cart }, { upsert: true });
  }

  console.log('Seed complete. Inserted customers and carts (idempotent).');
  process.exit(0);
}

seed().catch(err => {
  console.error('Seed failed:', err);
  process.exit(1);
});
