require('dotenv').config();
const { connect } = require('../db');
const Customer = require('../models/customer');
const { faker } = require('@faker-js/faker');

function normalizeAddress(a) {
  if (!a) return '';
  return a.toLowerCase().replace(/[.,]/g, '').replace(/\s+/g, ' ').trim();
}

function normalizePhone(p) {
  if (!p) return '';
  return p.replace(/[^0-9]/g, '');
}

async function seed() {
  await connect();
  console.log('Seeding customers...');
  // Idempotent: upsert by a synthetic "seedTag" + index
  const seedTag = 'sample13-v1';

  // Clear any previous sample docs with the seedTag marker
  await Customer.deleteMany({ 'meta.seedTag': seedTag });

  const products = ['toothpaste','coffee','shampoo','socks','notebook','tablet'];
  const docs = [];
  for (let i=0;i<20;i++) {
    const givenName = faker.person.firstName();
    const surname = faker.person.lastName();
    // create households by reusing addresses and phones for some customers
    const address = (i < 8) ? `100 Main St Apt ${Math.floor(i/4)+1}, Springfield` : (i < 14 ? `200 Oak Ave, Springfield` : `55 Elm St, Shelbyville`);
    const phone = (i % 6 === 0) ? '555-0100' : `555-01${(10 + (i%10)).toString().padStart(2,'0')}`;
    const clv = Math.round(Math.random() * 1000);
    const pCount = Math.ceil(Math.random()*3);
    const custProducts = [];
    for (let j=0;j<pCount;j++) {
      const pid = products[Math.floor(Math.random()*products.length)];
      custProducts.push({ productId: pid, name: pid, quantity: Math.ceil(Math.random()*3) });
    }
    docs.push({ givenName, surname, phone, address, normalizedAddress: normalizeAddress(address), clv, products: custProducts, meta: { seedTag } });
  }

  const res = await Customer.insertMany(docs);
  console.log(`Inserted ${res.length} customers.`);
  process.exit(0);
}

seed().catch(err => { console.error(err); process.exit(2); });
