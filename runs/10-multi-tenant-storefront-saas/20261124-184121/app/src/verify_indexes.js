// Lists indexes using Mongoose models
const { connect, disconnect, mongoose } = require('./mongoose');
const ProductSchema = require('./models/product');
const InventorySchema = require('./models/inventory');
const OrderSchema = require('./models/order');

async function main() {
  await connect();
  const Product = mongoose.model('Product', ProductSchema);
  const Inventory = mongoose.model('Inventory', InventorySchema);
  const Order = mongoose.model('Order', OrderSchema);

  console.log('Product indexes:');
  console.log(await Product.collection.indexes());
  console.log('Inventory indexes:');
  console.log(await Inventory.collection.indexes());
  console.log('Order indexes:');
  console.log(await Order.collection.indexes());

  await disconnect();
}

main().catch(err => { console.error(err); process.exit(1); });
