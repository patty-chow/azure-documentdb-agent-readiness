require('dotenv').config();
const express = require('express');
const bodyParser = require('body-parser');
const { seed } = require('./seed');
const { runForApplication } = require('./pipeline');
const { getDb } = require('./db');

const app = express();
app.use(bodyParser.json());

app.post('/seed', async (req, res) => {
  try {
    await seed();
    res.json({ status: 'ok', message: 'Seeded' });
  } catch (e) {
    res.status(500).json({ error: e.message });
  }
});

app.post('/run/:applicationId', async (req, res) => {
  try {
    const result = await runForApplication(req.params.applicationId);
    res.json(result);
  } catch (e) {
    res.status(500).json({ error: e.message });
  }
});

app.get('/applications/:id', async (req, res) => {
  try {
    const db = await getDb();
    const apps = db.collection('applications');
    const decisions = db.collection('decisions');
    const appDoc = await apps.findOne({ applicationId: req.params.id });
    const decision = await decisions.findOne({ applicationId: req.params.id });
    res.json({ application: appDoc, decision });
  } catch (e) {
    res.status(500).json({ error: e.message });
  }
});

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => console.log(`Server listening on ${PORT}`));

module.exports = app;
