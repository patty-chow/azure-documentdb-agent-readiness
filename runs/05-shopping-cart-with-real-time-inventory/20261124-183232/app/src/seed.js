const { connect, mongoose } = require('./db');
const { Inventory, Cart } = require('./models');

async function seed() {
  await connect();

  const products = [
    { sku: 'SKU-RED-001', name: 'Red T-Shirt', price: 19.99, stock: 5 },
    { sku: 'SKU-BLU-002', name: 'Blue Jeans', price: 49.99, stock: 2 },
    { sku: 'SKU-HAT-003', name: 'Cap', price: 12.5, stock: 10 }
  ];

  for (const p of products) {
    await Inventory.updateOne({ sku: p.sku }, { $set: p }, { upsert: true });
  }

  // Ensure a cart exists for demo user 'alice'
  await Cart.updateOne({ userId: 'alice' }, { $setOnInsert: { userId: 'alice', items: [] } }, { upsert: true });

  // Ensure indexes are created
  await Inventory.createCollection().catch(()=>{});
  await Cart.createCollection().catch(()=>{});
  await Inventory.syncIndexes();
  await Cart.syncIndexes();

  console.log('Seed complete');
  process.exit(0);
}

seed().catch(err=>{ console.error(err); process.exit(1); });
