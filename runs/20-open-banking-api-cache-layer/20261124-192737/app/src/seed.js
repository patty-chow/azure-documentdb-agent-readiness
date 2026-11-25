require('dotenv').config();
const { connect, disconnect } = require('./mongo');
const ApiCache = require('./models/ApiCache');

async function seed() {
  const uri = process.env.DOCUMENTDB_URI;
  if (!uri) throw new Error('DOCUMENTDB_URI not set in environment');
  await connect(uri);
  console.log('Connected, clearing any existing sample docs...');
  await ApiCache.deleteMany({});
  // Insert a sample cached response for key 'demo'
  const now = new Date();
  const expiresAt = new Date(Date.now() + 60 * 1000);
  const staleUntil = new Date(Date.now() + 360 * 1000);
  await ApiCache.create({ key: 'demo', response: { hello: 'world' }, statusCode: 200, headers: {}, cachedAt: now, expiresAt, staleUntil });
  console.log('Seeded sample document.');
  await disconnect();
}

seed().catch(err => { console.error(err); process.exit(1); });
