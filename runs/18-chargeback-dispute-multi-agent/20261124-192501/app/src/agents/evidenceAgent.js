const { getDb } = require('../db');

async function fetchEvidence(claimId) {
  const db = await getDb();
  const claimsColl = db.collection('claims');
  const transactionsColl = db.collection('transactions');
  const commsColl = db.collection('communications');

  const claim = await claimsColl.findOne({ claimId });
  if (!claim) throw new Error(`Claim ${claimId} not found`);

  // Fetch related transaction(s) and communications
  const transactions = await transactionsColl.find({ transactionId: claim.transactionId }).toArray();
  const communications = await commsColl.find({ claimId }).toArray();

  return { claim, transactions, communications };
}

module.exports = { fetchEvidence };
