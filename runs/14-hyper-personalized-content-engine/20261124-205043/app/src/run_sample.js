// Simple in-process sample runner that queries the agent for cust_1
const { getDb, getClient } = require('./db');
const { buildQueryEmbedding, retrieveAndRank, generateRationale } = require('./agent');

async function main() {
  const db = await getDb();
  const profile = await db.collection('profiles').findOne({ customerId: 'cust_1' });
  const segment = profile ? await db.collection('segments').findOne({ _id: profile.segmentId }) : null;
  const recent = await db.collection('interactions').find({ customerId: 'cust_1' }).sort({ timestamp: -1 }).limit(5).toArray();
  const dim = parseInt(process.env.EMBEDDING_DIM || '384', 10);
  const qEmb = await buildQueryEmbedding({ profile: profile || {}, interactions: recent, dim });
  const top = await retrieveAndRank({ db, queryEmbedding: qEmb, topK: 5 });
  const rationale = generateRationale({ profile: profile || { customerId: 'cust_1' }, segment, topItems: top });
  console.log('Rationale:\n', rationale);
  console.log('Top items:', top);
  const client = await getClient();
  await client.close();
}

main().catch((e) => { console.error(e); process.exit(1); });
