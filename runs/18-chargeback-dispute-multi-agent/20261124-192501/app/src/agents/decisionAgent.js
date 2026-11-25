const { getDb } = require('../db');

async function recordDecision(claimId, recommendation, rationale) {
  const db = await getDb();
  const decisions = db.collection('decisions');
  const now = new Date();
  const doc = {
    claimId,
    recommendation,
    rationale,
    createdAt: now,
    schemaVersion: 1
  };
  await decisions.insertOne(doc);
  return doc;
}

module.exports = { recordDecision };
