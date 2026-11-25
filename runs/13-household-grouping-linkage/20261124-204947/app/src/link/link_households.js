require('dotenv').config();
const { connect } = require('../db');
const Customer = require('../models/customer');
const Household = require('../models/household');
const mongoose = require('mongoose');

// Simple union-find to merge overlapping groups
class DSU {
  constructor(n) { this.p = Array.from({length:n}, (_,i)=>i); }
  find(a){ return this.p[a]===a?a:(this.p[a]=this.find(this.p[a])); }
  union(a,b){ a=this.find(a); b=this.find(b); if(a!==b) this.p[b]=a; }
}

async function linkHouseholds() {
  await connect();
  console.log('Linking households based on shared address or phone or surname+address');

  // Fetch sample customers (seeded ones) - we use all customers in our sample DB
  const customers = await Customer.find({});
  const n = customers.length;
  const dsu = new DSU(n);

  const addrMap = new Map();
  const phoneMap = new Map();
  const nameAddrMap = new Map();

  customers.forEach((c, idx) => {
    const a = c.normalizedAddress || '';
    const p = (c.phone || '').replace(/[^0-9]/g,'');
    const na = `${(c.surname||'').toLowerCase()}|${a}`;
    if (a) {
      if (!addrMap.has(a)) addrMap.set(a, []);
      addrMap.get(a).push(idx);
    }
    if (p) {
      if (!phoneMap.has(p)) phoneMap.set(p, []);
      phoneMap.get(p).push(idx);
    }
    if (na) {
      if (!nameAddrMap.has(na)) nameAddrMap.set(na, []);
      nameAddrMap.get(na).push(idx);
    }
  });

  function unionList(list) {
    for (let i=1;i<list.length;i++) dsu.union(list[0], list[i]);
  }

  for (const lst of addrMap.values()) if (lst.length>1) unionList(lst);
  for (const lst of phoneMap.values()) if (lst.length>1) unionList(lst);
  for (const lst of nameAddrMap.values()) if (lst.length>1) unionList(lst);

  // Build groups
  const groups = new Map();
  customers.forEach((c, idx) => {
    const root = dsu.find(idx);
    if (!groups.has(root)) groups.set(root, []);
    groups.get(root).push(customers[idx]._id);
  });

  // Persist households: idempotent based on members set
  let created = 0;
  for (const members of groups.values()) {
    // normalize members order for comparison
    const membersSorted = members.map(m=>m.toString()).sort();
    const existing = await Household.findOne({ 'meta.membersKey': membersSorted.join(',') });
    if (!existing) {
      const h = new Household({ members, meta: { membersKey: membersSorted.join(','), createdBy: 'seed-link' } });
      await h.save();
      created++;
    }
  }

  console.log(`Created ${created} new households.`);
  process.exit(0);
}

linkHouseholds().catch(err => { console.error(err); process.exit(2); });
