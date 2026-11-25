require('dotenv').config();
const express = require('express');
const bodyParser = require('body-parser');
const { handleNewClaim, decideExistingClaim } = require('./orchestrator');

const app = express();
app.use(bodyParser.json());

app.get('/health', (req, res) => res.json({ ok: true }));

app.post('/claims/submit', async (req, res) => {
  try {
    const payload = req.body;
    if (!payload || !payload.claimId || !payload.transactionId) {
      return res.status(400).json({ error: 'claimId and transactionId required' });
    }
    const result = await handleNewClaim(payload);
    res.json(result);
  } catch (err) {
    console.error(err);
    res.status(500).json({ error: err.message });
  }
});

app.post('/claims/:id/decide', async (req, res) => {
  try {
    const claimId = req.params.id;
    const result = await decideExistingClaim(claimId);
    res.json(result);
  } catch (err) {
    console.error(err);
    res.status(500).json({ error: err.message });
  }
});

const port = process.env.PORT || 3000;
app.listen(port, () => console.log(`Server listening on port ${port}`));
