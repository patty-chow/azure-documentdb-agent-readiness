jest.mock('../src/agents/copyAgent');
jest.mock('../src/agents/channelAgent');
jest.mock('../src/db');

const CopyAgent = require('../src/agents/copyAgent');
const ChannelAgent = require('../src/agents/channelAgent');
const { getDb } = require('../src/db');
const { runOnce } = require('../src/run');

describe('pipeline', () => {
  beforeEach(() => {
    // mock db collections
    const carts = {
      find: jest.fn().mockReturnValue({ toArray: async function() { return [{ _id: 'cart-1', customerId: 'cust-1', items: [{ name: 'X', qty: 1 }], status: 'abandoned', lastUpdated: new Date(0), sample: 'abandoned-cart-sample-12' }]; } }),
      createIndex: jest.fn()
    };
    const customers = { findOne: jest.fn().mockResolvedValue({ _id: 'cust-1', name: 'Test', email: 't@example.com', phone: '+1', preferredChannel: 'email' }) };
    const logs = { insertOne: jest.fn(), createIndex: jest.fn() };
    getDb.mockResolvedValue({ collection: (name) => { if (name==='carts') return carts; if (name==='customers') return customers; if (name==='recovery_logs') return logs; return {}; } });

    CopyAgent.mockImplementation(() => ({ generateMessage: jest.fn().mockResolvedValue('Hello Test, please complete your purchase') }));
    ChannelAgent.mockImplementation(() => ({ send: jest.fn().mockResolvedValue({ ok: true }) }));
  });

  it('runs the pipeline and logs outcomes', async () => {
    await runOnce();
    // if no exception, consider success; deeper assertions could be added
  }, 10000);
});
