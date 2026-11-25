const { MongoMemoryServer } = require('mongodb-memory-server');
const mongoose = require('mongoose');
const chai = require('chai');
const expect = chai.expect;
const Heartbeat = require('../models/heartbeat');
const AtmStatus = require('../models/atmStatus');
const { handleHeartbeat, recomputeSummary } = require('../logic/summaryUpdater');

let mongod;

describe('heartbeat logic', function() {
  this.timeout(10000);
  before(async () => {
    mongod = await MongoMemoryServer.create();
    const uri = mongod.getUri();
    await mongoose.connect(uri, { dbName: 'testdb' });
  });
  after(async () => {
    await mongoose.disconnect();
    await mongod.stop();
  });

  it('upserts atm status and computes summary', async () => {
    await Heartbeat.create({ atmId: 'ATM-001', status: 'online' });
    await handleHeartbeat({ atmId: 'ATM-001', status: 'online', timestamp: new Date() }, 0.5);
    let s = await recomputeSummary(0.5);
    expect(s.counts.online).to.equal(1);

    // Insert another atm offline
    await Heartbeat.create({ atmId: 'ATM-002', status: 'offline' });
    await handleHeartbeat({ atmId: 'ATM-002', status: 'offline', timestamp: new Date() }, 0.5);
    s = await recomputeSummary(0.5);
    expect(s.counts.offline).to.equal(1);
    expect(s.availability).to.be.closeTo(0.5, 0.001);
  });
});
