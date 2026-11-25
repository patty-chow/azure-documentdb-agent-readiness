require('dotenv').config();
const { connect } = require('../src/db');
const Interaction = require('../src/models/interaction');

async function run() {
  await connect();
  const res = await Interaction.syncIndexes();
  console.log('Sync indexes result:', res);
  process.exit(0);
}

run().catch(err => { console.error(err); process.exit(1); });
