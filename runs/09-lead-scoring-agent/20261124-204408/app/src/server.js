require('dotenv').config();
const express = require('express');
const bodyParser = require('body-parser');
const { scoreLead } = require('./scoreLead');

const app = express();
app.use(bodyParser.json());

app.post('/score-lead', async (req, res) => {
  const leadId = req.body.leadId;
  if (!leadId) return res.status(400).json({ error: 'leadId is required' });
  try {
    const updated = await scoreLead(leadId);
    res.json({ success: true, lead: updated });
  } catch (err) {
    console.error('Error scoring lead:', err);
    res.status(500).json({ error: err.message });
  }
});

const port = process.env.PORT || 3000;
app.listen(port, () => console.log(`Server listening on ${port}`));
