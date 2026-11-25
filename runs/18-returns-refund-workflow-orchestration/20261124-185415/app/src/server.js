const express = require('express');
const dotenv = require('dotenv');
dotenv.config();
const { processReturn } = require('./orchestration');

const app = express();
app.use(express.json());

app.post('/returns', async (req, res) => {
  const { orderId, reason, requester } = req.body;
  if (!orderId) return res.status(400).json({ error: 'orderId required' });
  try {
    const ret = await processReturn({ orderId, reason, requester });
    res.json(ret);
  } catch (e) {
    res.status(500).json({ error: e.message });
  }
});

if (require.main === module) {
  const port = process.env.PORT || 3000;
  app.listen(port, () => console.log('Server listening on', port));
}

module.exports = app;
