const express = require('express');
const dotenv = require('dotenv');
const { getDb } = require('./db');
const { buildQueryEmbedding, retrieveAndRank, generateRationale } = require('./agent');

dotenv.config();
const app = express();
app.use(express.json());

app.get('/search', async (req, res) => {
  const customerId = req.query.customerId;
  if (!customerId) return res.status(400).json({ error: 'customerId query param required' });
  const db = await getDb();
  const profiles = db.collection('profiles');
  const segments = db.collection('segments');
  const interactions = db.collection('interactions');

  const profile = await profiles.findOne({ customerId });
  const segment = profile ? await segments.findOne({ _id: profile.segmentId }) : null;
  const recent = await interactions.find({ customerId }).sort({ timestamp: -1 }).limit(5).toArray();

  const dim = parseInt(process.env.EMBEDDING_DIM || '384', 10);
  const qEmb = await buildQueryEmbedding({ profile: profile || {}, interactions: recent, dim });
  const top = await retrieveAndRank({ db, queryEmbedding: qEmb, topK: 5 });
  const rationale = generateRationale({ profile: profile || { customerId }, segment, topItems: top });

  res.json({ customerId, top, rationale });
});

const port = parseInt(process.env.PORT || '3000', 10);
app.listen(port, () => console.log(`Server listening on ${port}`));
