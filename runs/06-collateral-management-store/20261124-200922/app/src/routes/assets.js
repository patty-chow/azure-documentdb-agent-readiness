const express = require('express');
const router = express.Router();
const Collateral = require('../models/collateral');
const { classifyAsset } = require('../llm/classifier');

// POST /assets - create a new versioned document for an asset
router.post('/', async (req, res) => {
  try {
    const { assetId, valuation, metadata, embedding } = req.body;
    if (!assetId || !valuation || typeof valuation.amount !== 'number') {
      return res.status(400).json({ error: 'assetId and valuation.amount are required' });
    }

    // find current max version by querying and computing in JS (works with real Mongoose and mocks)
    const arr = await Collateral.find({ assetId });
    const latest = (arr && arr.length) ? arr.sort((a,b) => b.version - a.version)[0] : null;
    const nextVersion = latest ? latest.version + 1 : 1;

    const doc = new Collateral({
      assetId,
      version: nextVersion,
      valuation,
      metadata,
      embedding: embedding && Array.isArray(embedding) ? embedding : undefined
    });

    // Run LLM classification (may be disabled via env)
    const tags = await classifyAsset({ assetId, valuation, metadata });
    doc.llmTags = tags;

    await doc.save();
    return res.status(201).json(doc);
  } catch (err) {
    console.error('Error creating asset version:', err);
    return res.status(500).json({ error: 'internal_error', detail: err.message });
  }
});

// GET /assets/:assetId/history - return version history
router.get('/:assetId/history', async (req, res) => {
  try {
    const { assetId } = req.params;
    const history = await Collateral.find({ assetId });
    // ensure sorted
    const sorted = (history || []).sort((a,b) => b.version - a.version);
    return res.json(sorted);
  } catch (err) {
    console.error('Error fetching history:', err);
    return res.status(500).json({ error: 'internal_error' });
  }
});

module.exports = router;
