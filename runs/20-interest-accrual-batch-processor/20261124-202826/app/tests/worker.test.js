const { computeDailyAccrual } = require('../src/worker');

describe('accrual calculation', () => {
  test('daily accrual for 1 day', () => {
    const amount = computeDailyAccrual(1000, 5.0, 1); // $1000 at 5% APR
    expect(amount).toBeCloseTo( (1000 * 0.05) / 365 );
  });
});
