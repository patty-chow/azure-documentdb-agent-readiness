require('dotenv').config();
const mongoose = require('mongoose');
const { connect } = require('../src/db');

async function run() {
  await connect();
  console.log('Database name:', mongoose.connection.db.databaseName);
  const cols = await mongoose.connection.db.listCollections().toArray();
  console.log('Collections:', cols.map(c => c.name));
  process.exit(0);
}
run().catch(e => { console.error(e); process.exit(1); });
