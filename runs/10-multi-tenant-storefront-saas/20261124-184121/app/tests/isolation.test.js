// Integration test demonstrating tenant isolation. Runs against live cluster referenced by DOCUMENTDB_URI.
const { connect, disconnect, mongoose } = require('../src/mongoose');
const ProductSchema = require('../src/models/product');
const ProductRepo = require('../src/repos/productRepo');

async function run() {
  await connect();
  const Product = mongoose.model('Product', ProductSchema);

  // Ensure indexes exist
  await Product.createIndexes();

  // Create product for tenantB directly
  await Product.findOneAndUpdate({ tenantId: 'tenantB', sku: 'ISOL-1' }, { tenantId: 'tenantB', sku: 'ISOL-1', name: 'Isolation Product', price: 5.0 }, { upsert: true });

  // Use tenantA repository and ensure it cannot see tenantB's product
  const repoA = new ProductRepo(require('../src/models'), 'tenantA');
  const found = await repoA.findBySku('ISOL-1');
  if (found) {
    console.error('Isolation test failed: tenantA saw tenantB product');
    process.exit(2);
  }

  // Now verify that repository throws if tenantId omitted
  try {
    // Bypass repo to call model find without tenantId — the safety plugin should block this
    await Product.find({ sku: 'ISOL-1' });
    console.error('Safety plugin failed: query without tenantId succeeded');
    process.exit(3);
  } catch (err) {
    console.log('Safety plugin prevented query without tenantId (expected):', err.message);
  }

  console.log('Isolation test passed');
  await disconnect();
}

run().catch(err => { console.error(err); process.exit(1); });
