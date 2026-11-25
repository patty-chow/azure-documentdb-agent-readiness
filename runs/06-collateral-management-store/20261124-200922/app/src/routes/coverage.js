const express = require('express');
const router = express.Router();
const Collateral = require('../models/collateral');

// GET /coverage?totalLiabilities=12345&eligibleOnly=true
router.get('/', async (req, res) => {
  try {
    const totalLiabilities = Number(req.query.totalLiabilities || req.body?.totalLiabilities || 0);
    const eligibleOnly = req.query.eligibleOnly !== 'false';

    if (!totalLiabilities || isNaN(totalLiabilities)) {
      return res.status(400).json({ error: 'totalLiabilities query parameter is required and must be a number' });
    }

    // Aggregation: group by assetId and take the doc with max version
    // Then optionally filter by eligibilityTier != 'ineligible' or by provided eligibleOnly flag
    const pipeline = [
      { $sort: { assetId: 1, version: -1, createdAt: -1 } },
      {
        $group: {
          _id: '$assetId',
          doc: { $first: '$$ROOT' }
        }
      },
      { $replaceRoot: { newRoot: '$doc' } }
    ];

    if (eligibleOnly) {
      // treat ineligible explicitly
      pipeline.push({ $match: { 'llmTags.eligibilityTier': { $ne: 'ineligible' } } });
    }

    pipeline.push({
      $group: {
        _id: null,
        totalCollateral: { $sum: '$valuation.amount' },
        count: { $sum: 1 }
      }
    });

    const result = await Collateral.aggregate(pipeline);
    const totalCollateral = (result[0] && result[0].totalCollateral) || 0;
    const ratio = totalLiabilities === 0 ? null : totalCollateral / totalLiabilities;

    return res.json({ totalCollateral, totalLiabilities, coverageRatio: ratio, count: result[0]?.count || 0 });
  } catch (err) {
    console.error('Error computing coverage:', err);
    return res.status(500).json({ error: 'internal_error' });
  }
});

module.exports = router;
