import { jest } from '@jest/globals';
import * as dbModule from '../src/db.js';

jest.mock('../src/db.js', () => {
  return {
    getDb: jest.fn().mockResolvedValue({
      collection: () => ({ createIndex: jest.fn(), updateOne: jest.fn() })
    }),
    closeClient: jest.fn().mockResolvedValue()
  };
});

test('seed runs without throwing', async () => {
  const seed = await import('../src/seed.js');
  // seed script runs on import and will have called getDb; ensure import didn't throw
  expect(seed).toBeTruthy();
});
