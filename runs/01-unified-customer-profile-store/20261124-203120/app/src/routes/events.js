const express = require('express');
const router = express.Router();

module.exports = (CustomerProfileModel) => {
  router.post('/', async (req, res) => {
    try {
      const { source, customerId, attributes } = req.body;
      if (!source || !customerId || !attributes) {
        return res.status(400).json({ error: 'source, customerId, and attributes are required' });
      }
      const result = await CustomerProfileModel.upsertFromEvent({ source, customerId, attributes });
      return res.json({ ok: true, result });
    } catch (err) {
      console.error(err);
      return res.status(500).json({ error: err.message });
    }
  });

  return router;
};
