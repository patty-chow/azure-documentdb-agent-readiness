const express = require('express');
const { getDb } = require('./db');
const app = express();
require('dotenv').config();
const PORT = process.env.PORT || 3000;

app.get('/logs', async (req, res) => {
  const db = await getDb();
  const logs = await db.collection('outreach_logs').find().sort({ sentAt: -1 }).limit(50).toArray();
  res.json({ count: logs.length, logs });
});

if (require.main === module) {
  app.listen(PORT, () => console.log(`Server listening on ${PORT}`));
}

module.exports = app;
