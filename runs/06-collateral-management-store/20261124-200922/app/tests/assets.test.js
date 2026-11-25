const request = require('supertest');
const expressApp = require('../src/index');
const Collateral = require('../src/models/collateral');

let inMemory = {};

beforeEach(() => {
  inMemory = {}; // assetId -> [versions]

  // Mock findOne sorted by version
  Collateral.findOne = jest.fn(async (query) => {
    const assetId = query.assetId;
    const arr = inMemory[assetId] || [];
    if (arr.length === 0) return null;
    // return highest version
    return arr.reduce((a,b) => a.version > b.version ? a : b);
  });

  Collateral.find = jest.fn(async (query) => {
    // if query is empty, return all documents
    if (!query || Object.keys(query).length === 0) {
      return Object.values(inMemory).flat();
    }
    const assetId = query.assetId;
    return (inMemory[assetId] || []).slice().sort((a,b) => b.version - a.version);
  });

  Collateral.prototype.save = jest.fn(async function() {
    const doc = this.toObject ? this.toObject() : this;
    if (!inMemory[doc.assetId]) inMemory[doc.assetId] = [];
    inMemory[doc.assetId].push(doc);
    return doc;
  });

  Collateral.aggregate = jest.fn(async (pipeline) => {
    // simplistic implementation matching the pipeline used in sample
    // get latest per asset
    const latests = Object.values(inMemory).map(arr => arr.slice().sort((a,b) => b.version - a.version)[0]);
    let filtered = latests;
    const matchStage = pipeline.find(s => s['$match']);
    if (matchStage && matchStage['$match']['llmTags.eligibilityTier'] && matchStage['$match']['llmTags.eligibilityTier']['$ne'] === 'ineligible') {
      filtered = filtered.filter(d => (d.llmTags && d.llmTags.eligibilityTier) !== 'ineligible');
    }
    const totalCollateral = filtered.reduce((s,d) => s + (d.valuation?.amount || 0), 0);
    return [{ totalCollateral, count: filtered.length }];
  });
});

afterEach(() => {
  jest.resetAllMocks();
});

test('POST /assets creates versions and history returns them', async () => {
  const agent = request(expressApp);
  const payload = { assetId: 'T-1', valuation: { amount: 1000, currency: 'USD' }, metadata: { category: 'cash' } };
  const resp1 = await agent.post('/assets').send(payload).expect(201);
  expect(resp1.body.assetId).toBe('T-1');
  expect(resp1.body.version).toBe(1);

  const resp2 = await agent.post('/assets').send(Object.assign({}, payload, { valuation: { amount: 1200, currency: 'USD' } })).expect(201);
  expect(resp2.body.version).toBe(2);

  const hist = await agent.get('/assets/T-1/history').expect(200);
  expect(hist.body.length).toBe(2);
  expect(hist.body[0].version).toBe(2);
});

test('GET /coverage computes ratio', async () => {
  const agent = request(expressApp);
  await agent.post('/assets').send({ assetId: 'C-1', valuation: { amount: 5000, currency: 'USD' } }).expect(201);
  await agent.post('/assets').send({ assetId: 'C-2', valuation: { amount: 15000, currency: 'USD' } }).expect(201);

  const resp = await agent.get('/coverage').query({ totalLiabilities: 10000 }).expect(200);
  expect(resp.body.totalCollateral).toBe(20000);
  expect(resp.body.coverageRatio).toBe(2);
});
