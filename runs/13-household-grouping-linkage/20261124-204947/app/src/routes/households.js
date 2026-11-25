const express = require('express');
const router = express.Router();
const Household = require('../models/household');
const Customer = require('../models/customer');
const { Types } = require('mongoose');

// Get household CLV total
router.get('/:id/clv', async (req, res) => {
  try {
    const h = await Household.findById(req.params.id).populate('members');
    if (!h) return res.status(404).json({ error: 'Household not found' });
    const clvTotal = h.members.reduce((s, m) => s + (m.clv || 0), 0);
    res.json({ householdId: h._id, clvTotal });
  } catch (err) {
    console.error(err);
    res.status(500).json({ error: 'server_error' });
  }
});

// Get household aggregated product holdings
router.get('/:id/products', async (req, res) => {
  try {
    const h = await Household.findById(req.params.id);
    if (!h) return res.status(404).json({ error: 'Household not found' });
    // Aggregate products across member ids
    const agg = await Customer.aggregate([
      { $match: { _id: { $in: h.members.map(id => Types.ObjectId(id)) } } },
      { $unwind: '$products' },
      { $group: { _id: '$products.productId', name: { $first: '$products.name' }, totalQty: { $sum: '$products.quantity' }, count: { $sum: 1 } } },
      { $project: { productId: '$_id', name: 1, totalQty: 1, count: 1, _id: 0 } }
    ]);
    res.json({ householdId: h._id, products: agg });
  } catch (err) {
    console.error(err);
    res.status(500).json({ error: 'server_error' });
  }
});

module.exports = router;
