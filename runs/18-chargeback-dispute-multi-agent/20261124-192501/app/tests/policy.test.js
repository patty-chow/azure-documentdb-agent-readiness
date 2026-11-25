const { evaluateEvidence } = require('../src/agents/policyAgent');

test('policy accepts small amount', async () => {
  const evidence = { transaction: { amount: 50 } };
  const res = await evaluateEvidence(evidence);
  expect(res.decision).toBe('accept');
});

test('policy rejects large amount', async () => {
  const evidence = { transaction: { amount: 5000 } };
  const res = await evaluateEvidence(evidence);
  expect(res.decision).toBe('reject');
});
