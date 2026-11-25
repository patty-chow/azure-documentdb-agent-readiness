import { jest } from '@jest/globals';

// Basic unit test that mocks db access and LLM/channel agents

jest.unstable_mockModule('../src/agents/copyAgent.js', () => ({
  generateMessage: jest.fn(async ({ customer, cart }) => `Hello ${customer.name}, you left ${cart.items.length} items.`)
}));

jest.unstable_mockModule('../src/agents/channelAgent.js', () => ({
  sendNotification: jest.fn(async ({ customer, channel, message }) => ({ status: 'ok', provider: 'sim', providerId: 'sim-1' }))
}));

jest.unstable_mockModule('../src/db.js', () => ({
  getClientAsync: jest.fn(async () => ({
    db: () => ({
      collection: (name) => {
        if (name === 'carts') {
          return {
            find: () => ({
              hasNext: async () => false
            })
          };
        }
        if (name === 'customers') {
          return { findOne: async () => null };
        }
        if (name === 'notifications') {
          return { insertOne: async () => null };
        }
        return {};
      }
    })
  })),
  closeClient: jest.fn()
}));

const { runOnce } = await import('../src/pipeline.js');

test('runOnce runs without throwing when no carts', async () => {
  const res = await runOnce();
  expect(Array.isArray(res)).toBe(true);
  expect(res.length).toBe(0);
});
