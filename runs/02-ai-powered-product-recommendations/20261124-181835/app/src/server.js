/*
  server.js

  Purpose:
  - Provide an Express server that serves a simple UI for product recommendations.
  - Implement /recommend endpoint that returns top-5 recommendations with reasoning.
  - Persist per-session memory in the 'sessions' collection.

  High-level algorithm for /recommend:
  - Accept productId and session cookie.
  - Find the product and its embedding.
  - Use DocumentDB $search with cosmosSearch vector query to find nearest neighbors (k=10), filter out same product.
  - Use orders co-purchase signal (optional) and session memory to re-rank top results.
  - Ask OpenAI LLM for a brief explanation when OPENAI_API_KEY is available; otherwise return a templated reasoning.
*/

const express = require('express');
const cookieParser = require('cookie-parser');
const dotenv = require('dotenv');
dotenv.config();

const { getDb, getCollection, getClient } = require('./db');
const fetch = require('node-fetch');
const crypto = require('crypto');

const OPENAI_KEY = process.env.OPENAI_API_KEY;
const EMBEDDING_DIMS = parseInt(process.env.EMBEDDING_DIMS || '1536', 10);

const app = express();
app.use(express.json());
app.use(cookieParser());
app.use(express.static('public'));

/**
 * Utility: create a new random session id and persist initial memory.
 */
async function createSession(db) {
  const sid = crypto.randomBytes(12).toString('hex');
  const sessions = db.collection('sessions');
  await sessions.insertOne({ sessionId: sid, viewed: [], createdAt: new Date() });
  return sid;
}

/**
 * Utility: record that the session viewed a product (append to viewed list, bounded size).
 */
async function recordViewedProduct(db, sessionId, productId) {
  const sessions = db.collection('sessions');
  await sessions.updateOne({ sessionId }, { $push: { viewed: { $each: [productId], $slice: -20 } } }, { upsert: true });
}

/**
 * Utility: get session memory (viewed list) by sessionId.
 */
async function getSessionMemory(db, sessionId) {
  const sessions = db.collection('sessions');
  const s = await sessions.findOne({ sessionId });
  return s ? s.viewed || [] : [];
}

/**
 * Helper: call OpenAI completion for reasoning about recommendations. Falls back to templated text if key missing.
 */
async function explainRecommendations(product, recommendations, sessionMemory) {
  if (!OPENAI_KEY) {
    // Templated explanation when no LLM is available
    return `Recommended ${recommendations.length} items based on co-purchases and vector similarity to ${product.productId}. Session saw ${sessionMemory.length} items recently.`;
  }
  // Prepare a compact prompt for reasoning
  const prompt = `We have a seed product: ${product.productId} (${product.title}).

Top recommendations:
${recommendations.map((r, i) => `${i+1}. ${r.productId} - ${r.title}`).join('\n')}

Session recently viewed: ${sessionMemory.join(', ')}

Provide a short (2-3 sentence) explanation why these items are recommended.`;

  const res = await fetch('https://api.openai.com/v1/chat/completions', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${OPENAI_KEY}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      model: 'gpt-4o-mini',
      messages: [{ role: 'user', content: prompt }],
      max_tokens: 150,
      temperature: 0.7
    })
  });
  if (!res.ok) {
    const txt = await res.text();
    console.warn('OpenAI reasoning failed:', txt);
    return 'Explanation service failed; showing template explanation.';
  }
  const data = await res.json();
  return data.choices?.[0]?.message?.content || 'No explanation returned.';
}

/**
 * Recommendation endpoint.
 * - Request body: { productId }
 * - Returns: { recommendations: [{productId,title}], explanation }
 */
app.post('/api/recommend', async (req, res) => {
  try {
    const db = await getDb();
    const { productId } = req.body || {};
    if (!productId) return res.status(400).json({ error: 'productId is required' });

    // Session handling via cookie
    let sessionId = req.cookies.sessionId;
    if (!sessionId) {
      sessionId = await createSession(db);
      res.cookie('sessionId', sessionId, { httpOnly: true });
    }

    // Find the product document (need its embedding)
    const products = db.collection('products');
    const product = await products.findOne({ productId });
    if (!product) return res.status(404).json({ error: 'product not found' });

    // Ensure embedding exists
    if (!product.embedding) return res.status(500).json({ error: 'product has no embedding' });

    // Use $search with cosmosSearch (vector) to find neighbors.
    // The exact shape for cosmosSearch vector queries may vary by server; use $search with a 'knn' clause.
    const k = 10;
    const pipeline = [
      {
        $search: {
          knnBeta: {
            vector: product.embedding,
            path: 'embedding',
            k
          }
        }
      },
      { $limit: k + 1 }, // fetch a few more, we'll filter the same product
      { $project: { productId: 1, title: 1, score: { $meta: 'searchScore' } } }
    ];
    const cursor = products.aggregate(pipeline, { allowDiskUse: true });
    const results = await cursor.toArray();

    // Filter out the same product and take top 10
    const filtered = results.filter(r => r.productId !== productId).slice(0, 10);

    // Re-rank using simple co-purchase heuristic: count how often recommended item co-occurs with the seed in orders.
    const orders = db.collection('orders');
    const recIds = filtered.map(f => f.productId);
    // Aggregate co-purchase counts
    const counts = await orders.aggregate([
      { $match: { products: { $in: [productId] } } },
      { $unwind: '$products' },
      { $match: { products: { $in: recIds } } },
      { $group: { _id: '$products', count: { $sum: 1 } } }
    ]).toArray();
    const countMap = Object.fromEntries(counts.map(c => [c._id, c.count]));

    // Apply score = vector score + co-purchase weight + session boost/penalty
    const sessionMemory = await getSessionMemory(db, sessionId);
    const scored = filtered.map(r => {
      const vecScore = r.score || 0;
      const co = countMap[r.productId] || 0;
      const sessionBoost = sessionMemory.includes(r.productId) ? 0.2 : 0;
      const score = vecScore + Math.log(1 + co) * 0.3 + sessionBoost;
      return { ...r, score };
    }).sort((a, b) => b.score - a.score);

    const top = scored.slice(0, 5);

    // Persist that the session viewed the seed product
    await recordViewedProduct(db, sessionId, productId);

    const explanation = await explainRecommendations(product, top, sessionMemory);

    res.json({ recommendations: top.map(t => ({ productId: t.productId, title: t.title })), explanation });
  } catch (err) {
    console.error('recommend error', err);
    res.status(500).json({ error: String(err) });
  }
});

// Simple health endpoint
app.get('/health', (req, res) => res.json({ ok: true }));

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => console.log(`Server listening on http://localhost:${PORT}`));
