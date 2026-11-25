// Simple compliance agent — uses deterministic checks unless OPENAI_API_KEY provided
const { Configuration, OpenAIApi } = require('openai');
require('dotenv').config();

const OPENAI_API_KEY = process.env.OPENAI_API_KEY;
const OPENAI_MODEL = process.env.OPENAI_MODEL || 'gpt-4o-mini';

let openaiClient;
if (OPENAI_API_KEY) {
  const configuration = new Configuration({ apiKey: OPENAI_API_KEY });
  openaiClient = new OpenAIApi(configuration);
}

async function check(application) {
  const issues = [];
  if (!application.employment || application.employment.length === 0) {
    issues.push('No employment history provided');
  }
  if (!application.documents || application.documents.length === 0) {
    issues.push('Missing supporting documents');
  }
  const passed = issues.length === 0;
  let rationale = `Deterministic checks: ${issues.length} issues found.`;

  if (openaiClient) {
    try {
      const prompt = `You are a compliance reviewer. Given application ${JSON.stringify(application)}, list any compliance issues briefly.`;
      const res = await openaiClient.createChatCompletion({
        model: OPENAI_MODEL,
        messages: [{ role: 'user', content: prompt }],
        max_tokens: 200,
      });
      const text = res.data.choices?.[0]?.message?.content?.trim();
      if (text) rationale = text;
    } catch (e) {
      console.warn('OpenAI compliance call failed, using fallback:', e.message);
    }
  }

  return { passed, issues, rationale };
}

module.exports = { check };
