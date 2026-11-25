require('dotenv').config();
const express = require('express');
const { connect } = require('./db');
const Interaction = require('./models/interaction');
const { assessWithLLM } = require('./agent');

const app = express();
app.use(express.json());

app.post('/check-interactions', async (req, res) => {
  try {
    const meds = req.body.medications || [];
    if (!Array.isArray(meds) || meds.length < 2) return res.status(400).json({ error: 'Provide at least two medications' });

    await connect();

    // Normalize meds to lowercase trimmed names
    const normMeds = meds.map(m => String(m).trim().toLowerCase());

    // build unique sorted pairs
    const pairs = new Set();
    for (let i = 0; i < normMeds.length; i++) {
      for (let j = i + 1; j < normMeds.length; j++) {
        const a = normMeds[i];
        const b = normMeds[j];
        const sorted = [a,b].sort();
        pairs.add(sorted.join('|'));
      }
    }
    const pairList = Array.from(pairs);

    // fetch any existing interaction documents
    const docs = await Interaction.find({ normalizedPair: { $in: pairList } }).lean();
    const docMap = {};
    for (const d of docs) docMap[d.normalizedPair] = d;

    const results = [];
    for (const p of pairList) {
      const [a,b] = p.split('|');
      const doc = docMap[p];
      if (doc) {
        // If severityScore not present, ask LLM to rate using evidence
        let assessment = { severity: doc.severityScore ?? 0, recommendation: doc.clinicalRecommendation || '' };
        if (doc.severityScore == null || doc.clinicalRecommendation === '') {
          const llm = await assessWithLLM(d.drugA || a, d.drugB || b, doc.evidence || []);
          assessment = llm;
        }
        results.push({ drugA: a, drugB: b, normalizedPair: p, severity: assessment.severity, recommendation: assessment.recommendation, evidence: doc.evidence || [] });
      } else {
        // No document: attempt a heuristic or LLM with empty evidence
        const llm = await assessWithLLM(a, b, []);
        results.push({ drugA: a, drugB: b, normalizedPair: p, severity: llm.severity, recommendation: llm.recommendation, evidence: [] });
      }
    }

    // rank by severity desc
    results.sort((x,y) => y.severity - x.severity);
    res.json({ interactions: results });
  } catch (err) {
    console.error(err);
    res.status(500).json({ error: err.message });
  }
});

const port = process.env.PORT || 3000;
app.listen(port, () => console.log(`Server listening on ${port}`));
