const { assessWithLLM } = require('../src/agent');

test('heuristic fallback without OPENAI_API_KEY', async () => {
  delete process.env.OPENAI_API_KEY;
  const res = await assessWithLLM('aspirin','ibuprofen',['NSAIDs may interfere with aspirin platelet inhibition.']);
  expect(res).toHaveProperty('severity');
  expect(typeof res.severity).toBe('number');
});
