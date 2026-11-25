require('dotenv').config();
const express = require('express');
const bodyParser = require('body-parser');
const { handleMessage } = require('./agent');

const app = express();
app.use(bodyParser.json());

app.post('/chat', async (req, res) => {
  const { userId, message } = req.body;
  if (!userId || !message) return res.status(400).json({ error: 'userId and message required' });
  try {
    const out = await handleMessage(userId, message);
    res.json(out);
  } catch (err) {
    console.error(err);
    res.status(500).json({ error: String(err) });
  }
});

const port = process.env.PORT || 3000;
app.listen(port, () => console.log(`Server listening on ${port}`));
