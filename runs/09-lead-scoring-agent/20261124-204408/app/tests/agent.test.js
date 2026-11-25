const { buildPrompt } = require('../src/agent');

// Basic sanity test for prompt builder
test('buildPrompt includes lead name and signals', () => {
  const ctx = {
    lead: { leadId: 'lead-1', name: 'Alice', email: 'a@example.com' },
    company: { name: 'Alpha', industry: 'Software', size: 50 },
    recentActivities: [{ type: 'email_open', timestamp: new Date(), details: 'opened' }],
    engagement: [{ signal: 'marketing_score', value: 80 }]
  };
  const p = buildPrompt(ctx);
  expect(p).toContain('Alice');
  expect(p).toContain('marketing_score');
});
