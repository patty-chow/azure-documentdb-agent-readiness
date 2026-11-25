/*
  test_recommend.js
  One-shot script to verify recommendation pipeline against the live cluster.
*/

const { getDb, getClient } = require('./db');

async function run() {
  const db = await getDb();
  const products = db.collection('products');
  const seedProductId = 'P0';
  const product = await products.findOne({ productId: seedProductId });
  if (!product) return console.error('seed product not found');
  console.log('Found product', product.productId, product.title);
  const pipeline = [
    {
      $search: {
        knnBeta: {
          vector: product.embedding,
          path: 'embedding',
          k: 10
        }
      }
    },
    { $limit: 11 },
    { $project: { productId: 1, title: 1, score: { $meta: 'searchScore' } } }
  ];
  const res = await products.aggregate(pipeline, { allowDiskUse: true }).toArray();
  console.log('Top results:', res.slice(0,6));
  const client = await getClient();
  await client.close();
}

run().catch(e => { console.error(e); process.exit(1); });
