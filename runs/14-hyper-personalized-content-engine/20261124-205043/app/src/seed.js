/* Idempotent seed script: creates collections, inserts sample data, and creates a cosmosSearch vector index on content_pieces */
const { getDb, getClient } = require('./db');
const dotenv = require('dotenv');
const crypto = require('crypto');
dotenv.config();

const EMBEDDING_DIM = parseInt(process.env.EMBEDDING_DIM || '384', 10);

function deterministicVector(seed, dim) {
  // deterministic pseudo-random vector from seed string
  const h = crypto.createHash('sha256').update(seed).digest();
  const vec = new Array(dim);
  let acc = 0;
  for (let i = 0; i < dim; i++) {
    // expand hash deterministically
    const v = h[i % h.length] / 255;
    vec[i] = v;
    acc += v;
  }
  // normalize
  const norm = Math.sqrt(vec.reduce((s, x) => s + x * x, 0));
  return vec.map((x) => x / norm);
}

async function ensureCollections(db) {
  const existing = await db.listCollections().toArray();
  const names = existing.map((c) => c.name);
  const want = ['profiles', 'segments', 'interactions', 'content_pieces'];
  for (const n of want) {
    if (!names.includes(n)) {
      console.log('Creating collection', n);
      await db.createCollection(n);
    }
  }
}

async function upsertSampleData(db) {
  const profiles = db.collection('profiles');
  const segments = db.collection('segments');
  const interactions = db.collection('interactions');
  const content = db.collection('content_pieces');

  // segments
  await segments.updateOne(
    { _id: 'seg_1' },
    { $set: { _id: 'seg_1', name: 'High value shoppers', description: 'Customers with high lifetime spend' } },
    { upsert: true }
  );

  // profiles
  await profiles.updateOne(
    { customerId: 'cust_1' },
    {
      $set: {
        customerId: 'cust_1',
        name: 'Alice Example',
        email: 'alice@example.com',
        segmentId: 'seg_1',
        schemaVersion: 1
      }
    },
    { upsert: true }
  );

  // interactions (recent docs)
  const now = new Date();
  await interactions.updateOne(
    { _id: 'int_1' },
    {
      $set: {
        _id: 'int_1',
        customerId: 'cust_1',
        type: 'view',
        itemId: 'prod_42',
        timestamp: now
      }
    },
    { upsert: true }
  );

  // content pieces with deterministic embeddings
  const pieces = [
    { _id: 'c1', title: '10% off on electronics', body: 'Special offer on electronics for you', tags: ['promo', 'electronics'] },
    { _id: 'c2', title: 'How to choose a laptop', body: 'A buyer\'s guide to laptops', tags: ['guide', 'electronics'] },
    { _id: 'c3', title: 'Travel tips for 2025', body: 'Pack light and carry-on only', tags: ['travel'] },
    { _id: 'c4', title: 'Home office setup ideas', body: 'Ergonomic chairs and desks', tags: ['home'] }
  ];

  for (const p of pieces) {
    const emb = deterministicVector(p._id + '::' + p.title, EMBEDDING_DIM);
    await content.updateOne(
      { _id: p._id },
      { $set: { ...p, embedding: emb, embedding_model: 'mock', embedding_dim: EMBEDDING_DIM } },
      { upsert: true }
    );
  }
}

async function createVectorIndex(db) {
  // Create a cosmosSearch vector-hnsw index on content_pieces.embedding
  // We call the driver createIndex with the DocumentDB-specific cosmosSearchOptions
  const coll = db.collection('content_pieces');
  try {
    console.log('Creating vector index (cosmosSearch vector-hnsw) on content_pieces.embedding');
    await coll.createIndex(
      { embedding: 'cosmosSearch' },
      {
        name: 'content_embedding_hnsw',
        cosmosSearchOptions: {
          kind: 'vector-hnsw',
          dimensions: EMBEDDING_DIM,
          similarity: 'COS'
        }
      }
    );
    console.log('Index creation requested');
  } catch (e) {
    console.warn('index creation may have failed or already exist:', e.message);
  }
}

async function main() {
  const db = await getDb();
  await ensureCollections(db);
  await upsertSampleData(db);
  await createVectorIndex(db);
  // print counts
  const cols = ['profiles', 'segments', 'interactions', 'content_pieces'];
  for (const c of cols) {
    const count = await db.collection(c).countDocuments();
    console.log(`${c}: ${count} documents`);
  }
  const client = await getClient();
  await client.close();
  console.log('Seed complete');
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
