const { connect } = require('../src/db');
const { Event, Balance } = require('../src/models');

async function run() {
  await connect();
  const accountId = 'acct-1';
  const bal = await Balance.findOne({ accountId }).lean();
  console.log('Balance doc:', bal);
  const history = await Event.find({ accountId }).sort({ timestamp: 1 }).lean();
  console.log('History count:', history.length);
  if (history.length) console.log('First event:', history[0]);
  process.exit(0);
}

run().catch(err => { console.error(err); process.exit(1); });
