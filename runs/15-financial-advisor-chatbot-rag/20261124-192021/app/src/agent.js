const { getDb } = require('./db');

// Simple in-memory agent memory keyed by sessionId
const memoryStore = new Map();

function appendMemory(sessionId, message) {
  if (!memoryStore.has(sessionId)) memoryStore.set(sessionId, []);
  memoryStore.get(sessionId).push(message);
}

function getMemory(sessionId) {
  return memoryStore.get(sessionId) || [];
}

// Deterministic embedding generator (same algorithm as seed)
function seededRandom(seed) {
  let h = 2166136261 >>> 0;
  for (let i = 0; i < seed.length; i++) {
    h ^= seed.charCodeAt(i);
    h = Math.imul(h, 16777619);
  }
  return function () {
    h += 0x6D2B79F5;
    let t = Math.imul(h ^ (h >>> 15), 1 | h);
    t ^= t + Math.imul(t ^ (t >>> 7), 61 | t);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}
function makeEmbedding(seed, dims = 1536) {
  const rnd = seededRandom(seed);
  const vec = new Array(dims).fill(0).map(() => rnd());
  const norm = Math.sqrt(vec.reduce((s, v) => s + v * v, 0));
  return vec.map((v) => v / norm);
}

async function getEmbedding(text) {
  // If OPENAI_API_KEY is configured we could call OpenAI here. For simplicity
  // and to keep the sample runnable without keys we use deterministic local embedding
  if (process.env.OPENAI_API_KEY && process.env.USE_OPENAI_EMBEDDINGS === 'true') {
    // TODO: call OpenAI embeddings API
    // For now we fall back to local embedding
  }
  return makeEmbedding(text);
}

function cosine(a, b) {
  let dot = 0;
  for (let i = 0; i < a.length; i++) dot += a[i] * b[i];
  return dot; // because vectors are normalized, dot == cosine
}

async function retrieveRelevantDocs(query, topK = 3) {
  const db = await getDb();
  const coll = db.collection('knowledge');
  const qEmb = await getEmbedding(query);

  // For the small sample we fetch all docs and rank in-app. For production,
  // create a DocumentDB vector index and use $search + cosmosSearch.
  const cursor = coll.find({}, { projection: { title: 1, content: 1, embedding: 1, metadata: 1 } });
  const docs = await cursor.toArray();

  const scored = docs.map((d) => ({
    doc: d,
    score: cosine(qEmb, d.embedding || [])
  }));
  scored.sort((a, b) => b.score - a.score);
  return scored.slice(0, topK).map((s) => ({ ...s.doc, score: s.score }));
}

// Mocked portfolio tool
async function fetchPortfolio(clientId = 'demo-client') {
  // deterministic sample portfolio
  return {
    clientId,
    cash: 25000,
    totalValue: 250000,
    bondsAllocationPct: 40,
    equitiesAllocationPct: 55,
    othersPct: 5,
    bonds: [
      { ticker: 'MUNI-AAA', value: 60000, type: 'municipal', yield: 3.1 },
      { ticker: 'CORP-IG', value: 40000, type: 'corporate', yield: 4.2 }
    ]
  };
}

async function answerQuery(sessionId, query) {
  appendMemory(sessionId, { role: 'user', text: query });
  const memory = getMemory(sessionId);
  const relevant = await retrieveRelevantDocs(query, 3);
  const portfolio = await fetchPortfolio();

  // Simple answer composition: summarize findings and cite doc ids + portfolio numbers
  const summary = relevant.map((r, i) => `${i + 1}. ${r.title} (id=${r._id}, score=${r.score.toFixed(3)})`).join('\n');

  // naive relevance usage
  let text = `I found these relevant articles:\n${summary}\n`;
  text += `Your portfolio total value is $${portfolio.totalValue.toLocaleString()}, with ${portfolio.bondsAllocationPct}% in bonds (approx. $${Math.round((portfolio.bondsAllocationPct/100)*portfolio.totalValue).toLocaleString()}).\n`;

  // follow-up context: if last user message contains 'affect my bond allocation' or 'bond allocation', add tailored advice
  const lastUser = memory.slice().reverse().find(m => m.role === 'user');
  if (lastUser && /bond allocation|bond allocation\?|affect my bond/i.test(lastUser.text)) {
    text += `Based on the articles about bonds and municipal bonds, municipal bonds tend to be tax-advantaged and can be a lower-risk fixed-income allocation; consider whether tax treatment and credit quality match your goals. Given your current bond allocation (~${portfolio.bondsAllocationPct}%), small shifts (5-10%) toward higher-quality muni paper could modestly reduce taxable yield but lower volatility.`;
  } else {
    text += `If you want, I can analyze how a change to your bond allocation would change expected income — ask a follow-up like 'how does that affect my bond allocation?'`;
  }

  appendMemory(sessionId, { role: 'assistant', text });
  return { text, retrieved: relevant, portfolio };
}

module.exports = { answerQuery, retrieveRelevantDocs, appendMemory, getMemory };
