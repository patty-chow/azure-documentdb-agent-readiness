// Usage: node scripts/computeHousehold.js --id <householdId>
const mongoose = require('mongoose');
const argv = require('yargs').argv;
require('dotenv').config();
const CustomerSchema = require('../src/models/customer');
const HouseholdSchema = require('../src/models/household');

const uri = process.env.DOCUMENTDB_URI;
const dbName = process.env.DOCUMENTDB_DB || 'sample_customer_360_13';

async function main() {
  if (!argv.id) {
    console.error('Please pass --id <householdId>');
    process.exit(2);
  }
  await mongoose.connect(uri, { dbName });
  const Customer = mongoose.model('Customer', CustomerSchema);
  const Household = mongoose.model('Household', HouseholdSchema);
  const h = await Household.findById(argv.id).populate('members').exec();
  if (!h) {
    console.error('Household not found');
    process.exit(2);
  }
  const clvTotal = h.members.reduce((s, m) => s + (m.clv || 0), 0);
  const tally = {};
  h.members.forEach(m => (m.products || []).forEach(p => tally[p.productId] = (tally[p.productId]||0) + (p.quantity||1)));
  console.log(JSON.stringify({ householdId: argv.id, clvTotal, products: tally }, null, 2));
  await mongoose.disconnect();
}

main().catch(err => { console.error(err); process.exit(1); });
