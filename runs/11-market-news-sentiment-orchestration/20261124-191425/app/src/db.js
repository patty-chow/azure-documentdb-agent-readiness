const { MongoClient } = require('mongodb');
const { URL } = require('url');
const dotenv = require('dotenv');
dotenv.config();

const uri = process.env.DOCUMENTDB_URI;
if (!uri) throw new Error('DOCUMENTDB_URI is required in environment');

// Apply DocumentDB driver guidance: ensure tls=true and retryWrites=false if not present
function normalizeUri(raw) {
  try {
    const u = new URL(raw);
    // enforce tls (mongodb+srv is allowed)
    if (u.protocol === 'mongodb:') {
      // convert to mongodb+srv if already an SRV host isn't provided; leave as-is
    }
    // Append options if missing
    if (!u.searchParams.has('tls') && !u.searchParams.has('ssl')) {
      u.searchParams.set('tls', 'true');
    }
    if (!u.searchParams.has('retryWrites')) {
      u.searchParams.set('retryWrites', 'false');
    }
    return u.toString();
  } catch (e) {
    // not a full URL (maybe mongodb+srv style); return raw
    return raw;
  }
}

const normalizedUri = normalizeUri(uri);

// MongoClient recommended pattern: single shared client
const client = new MongoClient(normalizedUri, {
  // following documentdb-driver and connection guidance
  maxPoolSize: 50,
  minPoolSize: 0,
  connectTimeoutMS: 10000,
  serverSelectionTimeoutMS: 10000,
  monitorCommands: false
});

const DB_NAME = 'sample_fintech_11';

async function getDb() {
  if (!client.topology || !client.topology.isConnected()) {
    await client.connect();
  }
  return client.db(DB_NAME);
}

async function ensureIndexes() {
  const db = await getDb();
  const signals = db.collection('sentiment_signals');
  const watchlist = db.collection('watchlist');

  // create indexes idempotently
  await signals.createIndex({ tickers: 1 }, { name: 'idx_tickers' });
  await signals.createIndex({ timestamp: -1 }, { name: 'idx_timestamp' });
  // text index on headline for keyword queries
  try {
    await signals.createIndex({ headline: 'text' }, { name: 'idx_headline_text' });
  } catch (e) {
    // some DocumentDB clusters prefer textSearch; but createIndex('text') is supported in Mongo wire
    console.warn('text index creation returned:', e.message);
  }

  await watchlist.createIndex({ ticker: 1 }, { unique: true, name: 'idx_watchlist_ticker' });
}

module.exports = { client, getDb, ensureIndexes };
