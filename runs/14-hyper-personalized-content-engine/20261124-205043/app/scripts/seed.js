// Idempotent seed script: creates database collections and inserts sample documents with synthetic embeddings
const { getClient } = require('../src/db');

const DB_NAME = 'sample_customer_360_14';
const EMB_DIM = parseInt(process.env.EMBEDDING_DIM || '1536', 10);

function randomVector(dim) {
  // generate random vector and normalize to unit length
  const v = Array.from({ length: dim }, () => Math.random() - 0.5);
  const mag = Math.sqrt(v.reduce((s, x) => s + x * x, 0));
  return v.map(x => x / mag);
}

async function ensureSampleData() {
  const client = await getClient();
  const db = client.db(DB_NAME);

  const profiles = db.collection('profiles');
  const segments = db.collection('segments');
  const interactions = db.collection('interactions');
  const content = db.collection('content_pieces');

  // create sample segment
  await segments.updateOne({ _id: 'seg_premium' }, { $set: { name: 'Premium Shoppers', description: 'High-LTV customers' } }, { upsert: true });

  // profile
  await profiles.updateOne({ customerId: 'cust_1' }, {
    $set: {
      customerId: 'cust_1',
      name: 'Alice Example',
      segmentId: 'seg_premium',
      preferences: ['electronics', 'gadgets'],
      schemaVersion: 1
    }
  }, { upsert: true });

  // interactions (with embeddings)
  await interactions.updateOne({ _id: 'int_1' }, { $set: {
    _id: 'int_1', customerId: 'cust_1', type: 'view', occurredAt: new Date(), text: 'Interested in wireless earbuds', embedding: randomVector(EMB_DIM)
  }}, { upsert: true });

  // small content pieces
  const pieces = [];
  for (let i = 1; i <= 10; i++) {
    pieces.push({
      _id: `content_${i}`,
      title: `Gadget article ${i}`,
      body: `This is the body for gadget article ${i}.`,
      metadata: { category: 'electronics', tags: ['gadgets'] },
      embedding: randomVector(EMB_DIM),
      embedding_model: process.env.EMBEDDING_MODEL || 'synthetic',
      schemaVersion: 1
    });
  }

  for (const p of pieces) {
    await content.updateOne({ _id: p._id }, { $set: p }, { upsert: true });
  }

  console.log('Seed data inserted/updated.');
}

(async () => {
  try {
    await ensureSampleData();
    console.log('Seeding complete.');
  } catch (err) {
    console.error('Seed failed:', err);
    process.exit(1);
  } finally {
    process.exit(0);
  }
})();
