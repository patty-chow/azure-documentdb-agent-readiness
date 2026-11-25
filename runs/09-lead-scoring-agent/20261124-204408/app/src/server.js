const express = require('express');
const bodyParser = require('body-parser');
const { scoreLead } = require('./agent');

const app = express();
app.use(bodyParser.json());

app.post('/score-lead', async (req, res) => {
  const leadId = req.body.leadId || req.query.leadId;
  if (!leadId) return res.status(400).json({ error: 'leadId required' });
  try {
    const result = await scoreLead(leadId);
    res.json(result);
  } catch (err) {
    console.error(err);
    res.status(500).json({ error: String(err) });
  }
});

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => console.log(`Server listening on ${PORT}`));
