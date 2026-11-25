const { getDb, ensureIndexes } = require('./db');

async function seed() {
  const db = await getDb();
  await ensureIndexes();

  const customers = db.collection('customers');
  const carts = db.collection('carts');

  // sample customers
  const sampleCustomers = [
    { customerId: 'cust_1', name: 'Alice Smith', contactPreference: 'email', email: 'alice@example.com', phone: '+15550000001' },
    { customerId: 'cust_2', name: 'Bob Jones', contactPreference: 'sms', email: 'bob@example.com', phone: '+15550000002' },
    { customerId: 'cust_3', name: 'Carol Lee', contactPreference: 'email', email: 'carol@example.com', phone: '+15550000003' }
  ];

  for (const c of sampleCustomers) {
    await customers.updateOne({ customerId: c.customerId }, { $set: c }, { upsert: true });
  }

  // now seed carts. set updatedAt to now - varying hours so some are "abandoned"
  const now = new Date();
  const sampleCarts = [
    { cartId: 'cart_a', customerId: 'cust_1', items: [{ sku: 'SKU-RED-1', name: 'Red Shirt', qty: 1 }], updatedAt: new Date(now.getTime() - 1000 * 60 * 60 * 3), processedAt: null, deliveryLog: [] },
    { cartId: 'cart_b', customerId: 'cust_2', items: [{ sku: 'SKU-BLU-2', name: 'Blue Hat', qty: 2 }], updatedAt: new Date(now.getTime() - 1000 * 60 * 60 * 1), processedAt: null, deliveryLog: [] },
    { cartId: 'cart_c', customerId: 'cust_3', items: [{ sku: 'SKU-GRN-3', name: 'Green Socks', qty: 3 }], updatedAt: new Date(now.getTime() - 1000 * 60 * 60 * 5), processedAt: null, deliveryLog: [] },
    { cartId: 'cart_d', customerId: 'cust_1', items: [{ sku: 'SKU-YEL-4', name: 'Yellow Scarf', qty: 1 }], updatedAt: new Date(now.getTime() - 1000 * 60 * 30), processedAt: null, deliveryLog: [] }
  ];

  for (const cart of sampleCarts) {
    await carts.updateOne({ cartId: cart.cartId }, { $set: cart }, { upsert: true });
  }

  console.log('Seeding complete.');
  process.exit(0);
}

seed().catch(err => {
  console.error('Seed failed', err);
  process.exit(1);
});
