require('dotenv').config();
const { connect, disconnect } = require('./db');
const Bed = require('./models/bed');

async function ttlCheck() {
  await connect();
  const bed = await Bed.findOne({ wardId: 'ward-A' }).lean();
  if (!bed) {
    console.log('No bed found in ward-A to test TTL');
    await disconnect();
    return;
  }
  console.log('Using bed', bed.bedId);
  const expiresInSec = 5;
  const cleaningExpiresAt = new Date(Date.now() + expiresInSec * 1000);
  await Bed.updateOne({ _id: bed._id }, { $set: { status: 'cleaning', cleaningExpiresAt } });
  console.log('Set cleaningExpiresAt to', cleaningExpiresAt.toISOString());

  const checkUntil = Date.now() + 30000; // 30s
  while (Date.now() < checkUntil) {
    const doc = await Bed.findById(bed._id).lean();
    if (!doc) {
      console.log('Bed document has been deleted by TTL');
      await disconnect();
      return;
    }
    console.log('Still present at', new Date().toISOString());
    await new Promise(r => setTimeout(r, 3000));
  }
  console.log('TTL delete not observed within 30s; TTL deletions may be delayed by background thread interval');
  await disconnect();
}

ttlCheck().catch(err => {
  console.error(err);
  process.exit(1);
});
