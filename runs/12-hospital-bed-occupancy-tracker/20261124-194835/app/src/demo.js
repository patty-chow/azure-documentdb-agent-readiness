/**
 * Demo script: start watcher, perform a few status updates to trigger events, then exit.
 * Use: DOCUMENTDB_URI set in env. This script runs a transient change stream for ~12s.
 */
require('dotenv').config();
const { connect, disconnect } = require('./db');
const Bed = require('./models/bed');
const { startChangeWatcher } = require('./changeWatcher');

async function runDemo() {
  await connect();

  // Start change watcher for 12s
  const watcherPromise = startChangeWatcher(12000);

  // Give watcher a moment to start
  await new Promise(r => setTimeout(r, 1000));

  // Pick a sample ward and flip statuses on a few beds
  const wardId = 'ward-A';
  const beds = await Bed.find({ wardId }).limit(3);
  console.log('Demo will update beds:', beds.map(b => b.bedId));

  for (const b of beds) {
    const newStatus = b.status === 'available' ? 'occupied' : 'available';
    console.log(`Updating ${b.bedId} from ${b.status} -> ${newStatus}`);
    await Bed.updateOne({ _id: b._id }, { $set: { status: newStatus, lastStatusChangeAt: new Date(), cleaningExpiresAt: null } });
    await new Promise(r => setTimeout(r, 500));
  }

  // Simulate putting a bed into cleaning
  const bedToClean = beds[0];
  if (bedToClean) {
    const ttlSec = parseInt(process.env.CLEANING_TTL_SECONDS || '300', 10);
    const cleaningExpiresAt = new Date(Date.now() + ttlSec * 1000);
    console.log(`Setting ${bedToClean.bedId} status -> cleaning (expires in ${ttlSec}s)`);
    await Bed.updateOne({ _id: bedToClean._id }, { $set: { status: 'cleaning', lastStatusChangeAt: new Date(), cleaningExpiresAt } });
  }

  await watcherPromise;
  await disconnect();
  console.log('Demo finished');
}

runDemo().catch(err => {
  console.error(err);
  process.exit(1);
});
