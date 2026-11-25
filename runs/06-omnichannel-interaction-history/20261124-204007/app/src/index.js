require('dotenv').config();
const express = require('express');
const mongoose = require('mongoose');
const Interaction = require('./models/interaction');

const app = express();
app.use(express.json());

const DB_NAME = 'sample_customer_360_06';
const MONGO_URI = process.env.DOCUMENTDB_URI;
if (!MONGO_URI) {
  console.error('DOCUMENTDB_URI is not set. Copy .env.example to .env and set it.');
  process.exit(1);
}

async function connect() {
  // Connection options chosen for a long-running OLTP server per documented guidance
  await mongoose.connect(MONGO_URI, {
    dbName: DB_NAME,
    maxPoolSize: 50,
    minPoolSize: 10,
    connectTimeoutMS: 10000,
    socketTimeoutMS: 30000,
    serverSelectionTimeoutMS: 5000,
    retryWrites: true
  });
  // Ensure indexes are in sync with schema
  await Interaction.syncIndexes();
}

// Cursor encoding helpers: base64 JSON of {ts, id}
function encodeCursor(doc) {
  if (!doc) return null;
  const payload = { ts: doc.timestamp.toISOString(), id: doc._id.toString() };
  return Buffer.from(JSON.stringify(payload)).toString('base64');
}

function decodeCursor(cursor) {
  if (!cursor) return null;
  try {
    const json = Buffer.from(cursor, 'base64').toString('utf8');
    const obj = JSON.parse(json);
    return { ts: new Date(obj.ts), id: mongoose.Types.ObjectId(obj.id) };
  } catch (e) {
    return null;
  }
}

// GET /interactions/history?customerId=&limit=&cursor=
app.get('/interactions/history', async (req, res) => {
  const { customerId, limit = 20, cursor } = req.query;
  if (!customerId) return res.status(400).json({ error: 'customerId is required' });
  const pageSize = Math.min(200, parseInt(limit, 10) || 20);

  const decoded = decodeCursor(cursor);

  const match = { customerId };
  const sort = { timestamp: -1, _id: -1 };

  const filter = decoded ? {
    $and: [
      { customerId },
      { $or: [
        { timestamp: { $lt: decoded.ts } },
        { $and: [ { timestamp: decoded.ts }, { _id: { $lt: decoded.id } } ] }
      ] }
    ]
  } : match;

  const docs = await Interaction.find(filter).sort(sort).limit(pageSize + 1).exec();
  const hasMore = docs.length > pageSize;
  const pageDocs = hasMore ? docs.slice(0, pageSize) : docs;
  const nextCursor = hasMore ? encodeCursor(pageDocs[pageDocs.length - 1]) : null;

  res.json({ items: pageDocs, nextCursor });
});

// GET /interactions/channel-breakdown[?customerId=]
app.get('/interactions/channel-breakdown', async (req, res) => {
  const { customerId } = req.query;
  const pipeline = [];
  if (customerId) pipeline.push({ $match: { customerId } });
  pipeline.push({ $group: { _id: '$channel', count: { $sum: 1 } } });
  pipeline.push({ $project: { channel: '$_id', count: 1, _id: 0 } });
  const rows = await Interaction.aggregate(pipeline).exec();
  res.json({ breakdown: rows });
});

const PORT = process.env.PORT || 3000;
connect().then(() => {
  app.listen(PORT, () => console.log(`Server running on port ${PORT}`));
}).catch(err => {
  console.error('Failed to connect to DocumentDB:', err);
  process.exit(1);
});
