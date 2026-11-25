const { connect } = require('./db');
const Heartbeat = require('./models/heartbeat');
const AtmStatus = require('./models/atmStatus');
const { handleHeartbeat, recomputeSummary } = require('./logic/summaryUpdater');
const dotenv = require('dotenv');
dotenv.config();

const NUM_ATMS = parseInt(process.env.SEED_ATMS || '20', 10);
const THRESHOLD = parseFloat(process.env.AVAILABILITY_THRESHOLD || process.env.THRESHOLD || process.env.AVAILABILITY || '0.95');

async function seed() {
  await connect();
  console.log('Connected, seeding sample data...');

  // Create a set of ATM IDs
  const atms = Array.from({ length: NUM_ATMS }, (_, i) => `ATM-${String(i+1).padStart(3,'0')}`);

  // For idempotency, create a heartbeat per ATM with deterministic status based on index
  for (let i = 0; i < atms.length; i++) {
    const atmId = atms[i];
    const status = (i % 10 === 0) ? 'offline' : (i % 7 === 0 ? 'low_cash' : 'online');
    const hb = await Heartbeat.create({ atmId, status, cashLevel: Math.max(0, 100 - i), timestamp: new Date() });
    await handleHeartbeat({ atmId, status, timestamp: hb.timestamp }, THRESHOLD);
  }

  // Ensure indexes exist (Mongoose created them on model init, but call ensureIndexes)
  await Heartbeat.syncIndexes();
  await AtmStatus.syncIndexes();

  const summary = await recomputeSummary(THRESHOLD);
  console.log('Seed complete. Summary:', summary);
  process.exit(0);
}

seed().catch(err => { console.error(err); process.exit(2); });
