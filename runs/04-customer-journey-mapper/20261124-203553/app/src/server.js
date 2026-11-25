require('dotenv').config();
const express = require('express');
const { getCustomerJourney } = require('./aggregationTool');
const { summarizeJourney } = require('./agent');

const app = express();
app.use(express.json());

app.get('/journey', async (req, res) => {
  try {
    const customerId = req.query.customerId;
    if (!customerId) return res.status(400).json({ error: 'customerId query parameter is required' });
    const journey = await getCustomerJourney(customerId);
    const summary = await summarizeJourney(journey);
    return res.json({ journey, summary });
  } catch (err) {
    console.error(err);
    return res.status(500).json({ error: err.message });
  }
});

app.post('/journey', async (req, res) => {
  try {
    const customerId = req.body.customerId;
    if (!customerId) return res.status(400).json({ error: 'customerId body field is required' });
    const journey = await getCustomerJourney(customerId);
    const summary = await summarizeJourney(journey);
    return res.json({ journey, summary });
  } catch (err) {
    console.error(err);
    return res.status(500).json({ error: err.message });
  }
});

const port = process.env.PORT || 3000;
app.listen(port, () => {
  console.log(`Server listening on port ${port}`);
});
