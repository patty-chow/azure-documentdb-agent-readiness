// Small CLI helper that calls the same logic used by the server
require('dotenv').config();
const { connect } = require('../src/db');
const Interaction = require('../src/models/interaction');
const { assessWithLLM } = require('../src/agent');

async function run() {
  const meds = ['warfarin','aspirin','ibuprofen'];
  await connect();

  const norm = meds.map(m => String(m).trim().toLowerCase());
  const pairs = new Set();
  for (let i = 0; i < norm.length; i++) for (let j = i+1; j < norm.length; j++) pairs.add([norm[i],norm[j]].sort().join('|'));
  const pairList = Array.from(pairs);
  const docs = await Interaction.find({ normalizedPair: { $in: pairList } }).lean();
  for (const p of pairList) {
    const doc = docs.find(d => d.normalizedPair === p);
    if (doc) console.log('Found', p, '->', doc.severityScore, doc.clinicalRecommendation);
    else console.log('No document for', p);
  }
  process.exit(0);
}

run().catch(err => { console.error(err); process.exit(1); });
