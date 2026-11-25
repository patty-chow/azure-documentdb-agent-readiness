const { orchestrateClaim } = require('../src/orchestrator');

jest.mock('../src/agents/evidenceAgent', () => ({
  fetchEvidence: jest.fn(async (claimId) => ({
    claim: { claimId, transactionId: 'tx-1001' },
    transactions: [{ transactionId: 'tx-1001', amount: 125 }],
    communications: [{ text: 'Please refund' }]
  }))
}));

jest.mock('../src/agents/policyAgent', () => ({
  reasonPolicy: jest.fn(async (e) => ({ recommendation: 'accept', rationale: 'mocked' }))
}));

jest.mock('../src/agents/decisionAgent', () => ({
  recordDecision: jest.fn(async (claimId, rec, rationale) => ({ claimId, recommendation: rec, rationale }))
}));

test('orchestrator calls agents and returns structure', async () => {
  const result = await orchestrateClaim('claim-9001');
  expect(result).toHaveProperty('evidence');
  expect(result).toHaveProperty('policy');
  expect(result).toHaveProperty('decision');
  expect(result.policy.recommendation).toBe('accept');
});
