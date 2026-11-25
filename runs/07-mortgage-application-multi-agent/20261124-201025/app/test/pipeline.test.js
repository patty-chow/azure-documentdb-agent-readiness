const { MongoClient } = require('mongodb');
const { runForApplication } = require('../src/pipeline');
jest.mock('mongodb');

// Basic unit test that runs the pipeline with a mocked DB
describe('pipeline', () => {
  it('runs and writes a decision document', async () => {
    const fakeApp = {
      applicationId: 'test-1',
      name: 'Test User',
      income: 100000,
      liabilities: 10000,
      requested_amount: 200000,
      credit_score: 700,
      employment: [{ employer: 'TestCo', years: 3 }],
      documents: ['id']
    };

    const fakeDb = {
      collection: (name) => {
        return {
          findOne: async (q) => (name === 'applications' ? fakeApp : null),
          updateOne: async () => ({ upsertedId: 'd1' }),
        };
      }
    };

    // Mock getDb to return fakeDb
    jest.resetModules();
    jest.doMock('../src/db', () => ({ getDb: async () => fakeDb }));

    const pipeline = require('../src/pipeline');
    const result = await pipeline.runForApplication('test-1');
    expect(result).toHaveProperty('applicationId', 'test-1');
    expect(result).toHaveProperty('underwriting');
    expect(result).toHaveProperty('compliance');
    expect(result).toHaveProperty('letter');
  });
});
