const express = require('express');
const bodyParser = require('body-parser');
require('dotenv').config();
const Agent = require('./agent');

const app = express();
app.use(bodyParser.json());

const agent = new Agent();

app.post('/chat', async (req, res) => {
  try {
    const { patientId, message } = req.body;
    if (!patientId || !message) return res.status(400).json({ error: 'patientId and message required' });
    const result = await agent.process(patientId, message);
    res.json(result);
  } catch (err) {
    console.error(err);
    res.status(500).json({ error: 'internal_error' });
  }
});

const port = process.env.PORT || 3000;
app.listen(port, () => console.log(`Server listening on ${port}`));
