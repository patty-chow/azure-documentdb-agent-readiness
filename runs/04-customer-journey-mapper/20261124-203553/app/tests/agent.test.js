const { buildPrompt } = require('../src/agent');

test('buildPrompt includes events and channel groupings', () => {
  const journey = {
    customerId: 'cust_0001',
    timeline: [
      { timestamp: new Date('2023-01-01T10:00:00Z'), channel: 'web', eventType: 'view', metadata: {} },
      { timestamp: new Date('2023-01-03T12:00:00Z'), channel: 'email', eventType: 'click', metadata: {} }
    ],
    byChannel: { web: [{ timestamp: new Date('2023-01-01T10:00:00Z') }], email: [{ timestamp: new Date('2023-01-03T12:00:00Z') }] }
  };
  const prompt = buildPrompt(journey);
  expect(prompt).toMatch(/Customer ID: cust_0001/);
  expect(prompt).toMatch(/Structured timeline/);
  expect(prompt).toMatch(/Groupings by channel/);
});
