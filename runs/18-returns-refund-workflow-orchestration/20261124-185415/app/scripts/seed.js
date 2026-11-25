#!/usr/bin/env node
const { connect } = require('../src/db');
const Order = require('../src/models/order');

async function seed() {
  await connect();
  // create two orders: one low-value eligible, one high-value non-eligible for mock policy
  const orders = [
    {
      orderId: 'ORD-001',
      customerId: 'CUST-001',
      total: 49.99,
      currency: 'USD',
      items: [{ sku: 'SKU-RED-1', name: 'Red T-Shirt', qty: 1, price: 49.99 }],
      purchaseDate: new Date()
    },
    {
      orderId: 'ORD-002',
      customerId: 'CUST-002',
      total: 499.99,
      currency: 'USD',
      items: [{ sku: 'SKU-LAP-1', name: 'Laptop', qty: 1, price: 499.99 }],
      purchaseDate: new Date()
    }
  ];

  for (const o of orders) {
    try {
      await Order.updateOne({ orderId: o.orderId }, { $set: o }, { upsert: true });
      console.log('Upserted', o.orderId);
    } catch (e) {
      console.error('Failed to upsert', o.orderId, e.message);
    }
  }
  process.exit(0);
}

seed().catch(e => { console.error(e); process.exit(1); });
