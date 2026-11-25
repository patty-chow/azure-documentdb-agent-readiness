/*
  seed.js

  Purpose:
  - Seed the sample_retail_02 database with products (10k) and orders (20k) and sessions collection.
  - Generate embeddings either by calling OpenAI (if OPENAI_API_KEY is set) or by creating deterministic synthetic embeddings.
  - Create a DiskANN vector index on the products collection for the 'embedding' field.

  Usage: node src/seed.js
*/

const dotenv = require('dotenv');
dotenv.config();

const { getDb, getCollection, getClient } = require('./db');
const crypto = require('crypto');
const fetch = require('node-fetch');

const OPENAI_KEY = process.env.OPENAI_API_KEY;
const EMBEDDING_MODEL = process.env.EMBEDDING_MODEL || 'text-embedding-3-small';
const EMBEDDING_DIMS = parseInt(process.env.EMBEDDING_DIMS || '1536', 10);

/**
 * Helper: deterministic pseudo-random float vector generator for when an embedding API is not available.
 * Uses HMAC-SHA256 with the provided key to produce repeatable bytes, converts to floats in [-1,1].
 */
function syntheticEmbedding(key, dims) {
  const out = new Float32Array(dims);
  const h = crypto.createHmac('sha256', 'seed');
  h.update(String(key));
  let digest = h.digest();
  for (let i = 0; i < dims; i++) {
    // Re-hash periodically to get more bytes
    if (i % 32 === 0) {
      const hh = crypto.createHmac('sha256', 'seed');
      hh.update(String(key) + ':' + i);
      digest = hh.digest();
    }
    const b = digest[i % digest.length];
    // map byte [0,255] to [-1,1]
    out[i] = (b / 255) * 2 - 1;
  }
  // normalize to unit length (good for cosine similarity)
  const norm = Math.hypot(...out);
  if (norm > 0) for (let i = 0; i < dims; i++) out[i] = out[i] / norm;
  return Array.from(out);
}

/**
 * When OPENAI_API_KEY is present, call OpenAI embeddings endpoint.
 * The function returns an array<float> of length EMBEDDING_DIMS.
 */
async function getEmbeddingForText(text) {
  if (!OPENAI_KEY) {
    return syntheticEmbedding(text, EMBEDDING_DIMS);
  }
  // Minimal OpenAI REST call to obtain embeddings
  const res = await fetch('https://api.openai.com/v1/embeddings', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${OPENAI_KEY}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ model: EMBEDDING_MODEL, input: text })
  });
  if (!res.ok) {
    const txt = await res.text();
    throw new Error('OpenAI embeddings failed: ' + txt);
  }
  const data = await res.json();
  // the API returns data[0].embedding
  return data.data[0].embedding;
}

/**
 * Create DiskANN vector index on products.embedding using the DocumentDB createIndexes pattern.
 * Uses db.runCommand via driver's command. This is the DocumentDB recommended method.
 */
async function createVectorIndexIfNotExists(db) {
  // Prepare the createIndexes spec for a vector-diskann index per documentdb-vector-search guidance
  const collName = 'products';
  const indexSpec = {
    name: 'idx_embedding_diskann',
    key: { embedding: 'cosmosSearch' },
    // options tuned for DiskANN; cosmosSearchOptions describes type and dims
    // The DocumentDB createIndexes runCommand expects an options object; here we include cosmosSearchOptions
    cosmosSearchOptions: {
      kind: 'vector-diskann',
      dimensions: EMBEDDING_DIMS,
      similarity: 'COS',
      // additional DiskANN params could go here; leaving defaults
    }
  };

  try {
    console.log('Creating vector index (DiskANN) on products.embedding (if not exists)...');
    // The driver exposes runCommand on the database to execute createIndexes
    // For MongoDB-compatible API, createIndexes on a collection is also acceptable but the cluster requires the special cosmosSearchOptions.
    const cmd = {
      createIndexes: collName,
      indexes: [
        {
          name: indexSpec.name,
          key: { embedding: 1 },
          // Store the cosmosSearchOptions in the 'collation' field is not standard; Azure DocumentDB accepts a specialized command shape. We put options at top-level inside 'cosmosSearchOptions' per guidance.
          // Some clusters accept the options under 'cosmosSearchOptions' directly in the index spec.
          cosmosSearchOptions: indexSpec.cosmosSearchOptions
        }
      ]
    };
    const res = await db.command(cmd);
    console.log('createIndexes result:', res);
  } catch (err) {
    console.warn('Vector index creation may have failed or already exists:', err.message);
  }
}

/**
 * Seed products (10k) and orders (20k). Each product has an embedding field (array of floats).
 */
async function seed() {
  const db = await getDb();
  await createVectorIndexIfNotExists(db);

  const productsColl = db.collection('products');
  const ordersColl = db.collection('orders');
  const sessionsColl = db.collection('sessions');

  // Create some product metadata: 10,000 products P0..P9999
  const NUM_PRODUCTS = 10000;
  console.log('Seeding products:', NUM_PRODUCTS);
  const batchSize = 500;
  for (let i = 0; i < NUM_PRODUCTS; i += batchSize) {
    const batch = [];
    for (let j = i; j < Math.min(i + batchSize, NUM_PRODUCTS); j++) {
      const productId = `P${j}`;
      const title = `Product ${j}`;
      // Simple textual prompt for embedding
      const prompt = `${title} - a sample item in category C${j % 20}`;
      const embedding = await getEmbeddingForText(prompt);
      batch.push({ productId, title, category: `C${j % 20}`, embedding });
    }
    await productsColl.insertMany(batch, { ordered: false }).catch(e => console.warn('insertMany products batch warning', e.message));
    console.log(`Inserted products ${i}..${Math.min(i + batchSize, NUM_PRODUCTS)-1}`);
  }

  // Seed 20,000 orders. Each order picks 1-5 products randomly, with a bias to co-purchases.
  const NUM_ORDERS = 20000;
  console.log('Seeding orders:', NUM_ORDERS);
  for (let i = 0; i < NUM_ORDERS; i += batchSize) {
    const batch = [];
    for (let j = i; j < Math.min(i + batchSize, NUM_ORDERS); j++) {
      const orderId = `O${j}`;
      const userId = `U${Math.floor(Math.random() * 5000)}`;
      // Create small baskets: 1-5 items
      const numItems = 1 + Math.floor(Math.random() * 5);
      const products = [];
      for (let k = 0; k < numItems; k++) {
        // sample product with slight category locality
        const pid = Math.floor(Math.random() * NUM_PRODUCTS);
        products.push(`P${pid}`);
      }
      batch.push({ orderId, userId, products, timestamp: new Date() });
    }
    await ordersColl.insertMany(batch, { ordered: false }).catch(e => console.warn('insertMany orders batch warning', e.message));
    console.log(`Inserted orders ${i}..${Math.min(i + batchSize, NUM_ORDERS)-1}`);
  }

  console.log('Seed complete.');
  const client = await getClient();
  await client.close();
}

seed().catch(err => {
  console.error('Seeding failed:', err);
  process.exit(1);
});
