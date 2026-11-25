/* Seed script: idempotent-ish
   - inserts customers if none exist
   - creates households by grouping on normalizedAddress/phone/surname
*/
const { connect, mongoose } = require('../src/db');
const CustomerSchema = require('../src/models/customer');
const HouseholdSchema = require('../src/models/household');
const { faker } = require('@faker-js/faker');

const Customer = mongoose.model('Customer', CustomerSchema);
const Household = mongoose.model('Household', HouseholdSchema);

function normalizeAddress(a) {
  if (!a) return '';
  return `${(a.line1||'').trim().toLowerCase()}|${(a.city||'').trim().toLowerCase()}|${(a.postcode||'').trim().toLowerCase()}`;
}

async function main() {
  await connect();

  const db = mongoose.connection;
  const count = await Customer.countDocuments();
  if (count < 20) {
    console.log('Seeding customers...');
    const customers = [];
    // create some shared households
    const householdsSeed = [
      { line1: '12 Oak St', city: 'Seattle', postcode: '98101' },
      { line1: '99 Pine Ave', city: 'Seattle', postcode: '98102' },
      { line1: '5 Elm Rd', city: 'Redmond', postcode: '98052' }
    ];
    for (let i = 0; i < 20; i++) {
      const base = householdsSeed[i % householdsSeed.length];
      const address = { ...base };
      const normalizedAddress = normalizeAddress(address);
      const surname = faker.person.lastName();
      const phone = `+1-206-${Math.floor(1000000 + Math.random()*9000000).toString().slice(0,7)}`;
      const clv = Math.floor(Math.random()*10000);
      const products = [];
      const numProducts = Math.floor(Math.random()*4);
      for (let p=0;p<numProducts;p++) products.push({ productId: `P${Math.floor(1+Math.random()*10)}`, quantity: Math.floor(1+Math.random()*3) });
      customers.push({ firstName: faker.person.firstName(), lastName: faker.person.lastName(), surname, phone, address: {...address, normalizedAddress}, clv, products });
    }
    await Customer.insertMany(customers);
    console.log('Inserted customers');
  } else {
    console.log('Customers already seeded (count=',count,')');
  }

  // Create households by grouping customers that share normalizedAddress + phone + surname
  console.log('Aggregating groups for households...');
  const groups = await Customer.aggregate([
    { $match: { 'address.normalizedAddress': { $exists: true, $ne: '' } } },
    { $group: { _id: { addr: '$address.normalizedAddress', phone: '$phone', surname: '$surname' }, members: { $push: '$_id' }, count: { $sum: 1 } } },
    { $match: { count: { $gte: 1 } } }
  ]);

  console.log('Found', groups.length, 'groups');

  // For each group, either upsert a household document with these members
  for (const g of groups) {
    const members = g.members;
    // Attach household to if not exists with exactly same members
    const existing = await Household.findOne({ members: { $size: members.length, $all: members } });
    if (!existing) {
      const h = await Household.create({ members });
      console.log('Created household', h._id.toString(), 'members=', members.length);
    }
  }

  console.log('Seeding done.');
  await mongoose.disconnect();
}

main().catch(err => {
  console.error(err);
  process.exit(1);
});
