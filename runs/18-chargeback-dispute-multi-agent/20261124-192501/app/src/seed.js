const { getDb } = require('./db');

async function ensureIndexIfMissing(coll, spec, options) {
  const existing = await coll.indexes();
  const exists = existing.some(ix => {
    const keys = JSON.stringify(ix.key);
    return keys === JSON.stringify(spec);
  });
  if (!exists) {
    await coll.createIndex(spec, options);
  }
}

async function ensureIndexes(db) {
  await ensureIndexIfMissing(db.collection('transactions'), { transactionId: 1 }, { name: 'idx_transactionId', unique: false });
  await ensureIndexIfMissing(db.collection('transactions'), { createdAt: -1 }, { name: 'idx_tx_createdAt' });
  await ensureIndexIfMissing(db.collection('communications'), { claimId: 1 }, { name: 'idx_comm_claimId' });
  await ensureIndexIfMissing(db.collection('claims'), { claimId: 1 }, { name: 'idx_claim_claimId' });
  await ensureIndexIfMissing(db.collection('decisions'), { claimId: 1 }, { name: 'idx_decision_claimId' });
}

async function seed() {
  const db = await getDb();
  await ensureIndexes(db);

  const claims = db.collection('claims');
  const transactions = db.collection('transactions');
  const communications = db.collection('communications');

  // Upsert a sample transaction
  await transactions.updateOne(
    { transactionId: 'tx-1001' },
    { $set: { transactionId: 'tx-1001', amount: 125.00, currency: 'USD', createdAt: new Date(), schemaVersion: 1 } },
    { upsert: true }
  );

  // Upsert a sample claim
  await claims.updateOne(
    { claimId: 'claim-9001' },
    { $set: { claimId: 'claim-9001', transactionId: 'tx-1001', reason: 'unauthorized', createdAt: new Date(), schemaVersion: 1 } },
    { upsert: true }
  );

  // Upsert communications
  await communications.updateOne(
    { commId: 'c-1' },
    { $set: { commId: 'c-1', claimId: 'claim-9001', text: 'I did not make this purchase. Please refund.', createdAt: new Date(), schemaVersion: 1 } },
    { upsert: true }
  );

  console.log('Seeding complete');
}

seed().catch(err => {
  console.error('Seed failed', err);
  process.exit(1);
});
