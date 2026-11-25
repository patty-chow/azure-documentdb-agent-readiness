/* agent.js
 - builds a query embedding (mock) from profile+recent interactions
 - retrieves content pieces from DB and ranks by cosine similarity
 - returns a rationale and ranked items
*/
const crypto = require('crypto');

function deterministicVector(seed, dim) {
  const h = crypto.createHash('sha256').update(seed).digest();
  const vec = new Array(dim);
  for (let i = 0; i < dim; i++) {
    const v = h[i % h.length] / 255;
    vec[i] = v;
  }
  const norm = Math.sqrt(vec.reduce((s, x) => s + x * x, 0));
  return vec.map((x) => x / norm);
}

function cosineSimilarity(a, b) {
  let dot = 0;
  let na = 0;
  let nb = 0;
  for (let i = 0; i < a.length; i++) {
    dot += a[i] * b[i];
    na += a[i] * a[i];
    nb += b[i] * b[i];
  }
  if (na === 0 || nb === 0) return 0;
  return dot / (Math.sqrt(na) * Math.sqrt(nb));
}

async function buildQueryEmbedding({ profile, interactions, dim }) {
  // simple mock: combine deterministic vectors for profile and interaction items
  const parts = [];
  parts.push(deterministicVector('profile::' + (profile.customerId || 'anon'), dim));
  if (interactions && interactions.length) {
    for (const it of interactions) {
      parts.push(deterministicVector('interaction::' + (it.itemId || it._id || ''), dim));
    }
  }
  // average
  const res = new Array(dim).fill(0);
  for (const p of parts) {
    for (let i = 0; i < dim; i++) res[i] += p[i];
  }
  for (let i = 0; i < dim; i++) res[i] = res[i] / parts.length;
  // normalize
  const norm = Math.sqrt(res.reduce((s, x) => s + x * x, 0));
  return res.map((x) => x / norm);
}

async function retrieveAndRank({ db, queryEmbedding, topK = 5 }) {
  const content = db.collection('content_pieces');
  const docs = await content.find({}, { projection: { embedding: 1, title: 1, body: 1, tags: 1 } }).toArray();
  const scored = docs.map((d) => ({
    doc: d,
    score: cosineSimilarity(queryEmbedding, d.embedding || [])
  }));
  scored.sort((a, b) => b.score - a.score);
  return scored.slice(0, topK).map((s) => ({ id: s.doc._id, title: s.doc.title, score: s.score, body: s.doc.body }));
}

function generateRationale({ profile, segment, topItems }) {
  // Mock chat generator: short template-based rationale
  const reasons = [];
  reasons.push(`Customer ${profile.name || profile.customerId} is in segment ${segment ? segment.name : 'unknown'}.`);
  reasons.push(`Based on recent interactions and profile we prioritized content that matches their interests.`);
  const items = topItems.map((it, idx) => `${idx + 1}. "${it.title}" (score=${it.score.toFixed(3)})`);
  return `${reasons.join(' ')} Top recommended items:\n${items.join('\n')}`;
}

module.exports = { buildQueryEmbedding, retrieveAndRank, generateRationale };
