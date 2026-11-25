const express = require('express');
const dotenv = require('dotenv');
dotenv.config();

const { orchestrateClaim } = require('./orchestrator');

const app = express();
app.use(express.json());

app.get('/health', (req, res) => res.json({ status: 'ok' }));

app.post('/claims/:claimId/decide', async (req, res) => {
  const claimId = req.params.claimId;
  try {
    const result = await orchestrateClaim(claimId);
    res.json({ ok: true, result });
  } catch (err) {
    console.error(err);
    res.status(500).json({ ok: false, error: err.message });
  }
});

const port = process.env.PORT || 3000;
app.listen(port, () => console.log(`Server listening on ${port}`));
