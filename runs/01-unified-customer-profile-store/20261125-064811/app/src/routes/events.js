const express = require('express');
const router = express.Router();
const dbModule = require('../db');
const { upsertEvent } = require('../lib/upsert');

router.post('/', async (req, res) => {
  try {
    const { source, customerId, attributes } = req.body;
    if (!source || !customerId || !attributes) {
      return res.status(400).json({ error: 'Missing required fields: source, customerId, attributes' });
    }
    const db = await dbModule.connect();
    const result = await upsertEvent(db, { source, customerId, attributes });
    return res.json({ ok: true, result });
  } catch (err) {
    console.error('Error in /events:', err.message);
    return res.status(500).json({ error: err.message });
  }
});

module.exports = router;
