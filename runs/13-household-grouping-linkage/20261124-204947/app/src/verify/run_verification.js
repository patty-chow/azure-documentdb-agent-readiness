require('dotenv').config();
const { connect, mongoose } = require('../db');
const Customer = require('../models/customer');
const Household = require('../models/household');

async function run() {
  await connect();
  console.log('Listing sample counts:');
  const cCount = await Customer.countDocuments();
  const hCount = await Household.countDocuments();
  console.log(`customers: ${cCount}`);
  console.log(`households: ${hCount}`);
  // show sample household
  const h = await Household.findOne().limit(1).populate('members');
  if (h) {
    console.log('Sample household members:');
    h.members.forEach(m => console.log(` - ${m.givenName} ${m.surname} (${m._id}) CLV=${m.clv}`));
  } else {
    console.log('No household documents found. Run npm run link to create them.');
  }
  await mongoose.disconnect();
}

run().catch(err => { console.error(err); process.exit(2); });
