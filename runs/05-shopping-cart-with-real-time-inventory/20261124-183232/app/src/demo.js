const { connect } = require('./db');
const { Inventory } = require('./models');
const { addToCart } = require('./service');

async function demo() {
  await connect();
  // pick a product to test
  const prod = await Inventory.findOne({ sku: 'SKU-BLU-002' });
  if (!prod) { console.error('seed first (npm run seed)'); process.exit(1); }

  console.log('Product before:', prod.sku, 'stock=', prod.stock);

  // try to add more than stock to show clear error
  const overQty = prod.stock + 5;
  const r = await addToCart('alice', prod._id, overQty);
  console.log('Attempt add over stock result:', r);

  // now add a valid amount
  const okR = await addToCart('alice', prod._id, 1);
  console.log('Add 1 result:', okR.success ? 'ok' : okR);

  const after = await Inventory.findById(prod._id);
  console.log('Product after:', after.sku, 'stock=', after.stock);

  process.exit(0);
}

demo().catch(err=>{ console.error(err); process.exit(1); });
