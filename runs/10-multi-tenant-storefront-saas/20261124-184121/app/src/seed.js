const { connect, disconnect, mongoose } = require('./mongoose');
const ProductSchema = require('./models/product');
const InventorySchema = require('./models/inventory');
const OrderSchema = require('./models/order');

async function main() {
  await connect();

  // Register models on the mongoose connection used by the app
  const Product = mongoose.model('Product', ProductSchema);
  const Inventory = mongoose.model('Inventory', InventorySchema);
  const Order = mongoose.model('Order', OrderSchema);

  console.log('Creating indexes...');
  await Product.createIndexes();
  await Inventory.createIndexes();
  await Order.createIndexes();

  console.log('Seeding sample data...');

  const tenants = ['tenantA', 'tenantB'];

  // Idempotent upserts per tenant
  for (const t of tenants) {
    await Product.findOneAndUpdate({ tenantId: t, sku: 'SKU-100' }, { tenantId: t, sku: 'SKU-100', name: `Widget for ${t}`, price: 9.99 }, { upsert: true });
    await Product.findOneAndUpdate({ tenantId: t, sku: 'SKU-200' }, { tenantId: t, sku: 'SKU-200', name: `Gadget for ${t}`, price: 19.99 }, { upsert: true });

    await Inventory.updateOne({ tenantId: t, sku: 'SKU-100' }, { $set: { quantity: 100, updatedAt: new Date() }, $setOnInsert: { tenantId: t } }, { upsert: true });
    await Inventory.updateOne({ tenantId: t, sku: 'SKU-200' }, { $set: { quantity: 50, updatedAt: new Date() }, $setOnInsert: { tenantId: t } }, { upsert: true });

    await Order.create({ tenantId: t, orderNumber: `${t}-ORD-1`, items: [{ sku: 'SKU-100', qty: 2, price: 9.99 }], total: 19.98 });
  }

  console.log('Seed complete');
  await disconnect();
}

main().catch(err => {
  console.error(err);
  process.exit(1);
});
