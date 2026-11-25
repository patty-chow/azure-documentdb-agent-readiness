// Simple underwriting agent. If OPENAI_API_KEY is set, this module will attempt
// a simple LLM call; otherwise it uses deterministic rule-based logic.
const { Configuration, OpenAIApi } = require('openai');
require('dotenv').config();

const OPENAI_API_KEY = process.env.OPENAI_API_KEY;
const OPENAI_MODEL = process.env.OPENAI_MODEL || 'gpt-4o-mini';

let openaiClient;
if (OPENAI_API_KEY) {
  const configuration = new Configuration({ apiKey: OPENAI_API_KEY });
  openaiClient = new OpenAIApi(configuration);
}

async function assess(application) {
  // Deterministic fallback rules (works without LLM):
  const income = application.income || 0;
  const liabilities = application.liabilities || 0;
  const requested = application.requested_amount || 0;
  const credit = application.credit_score || 0;

  const affordability = (income - liabilities) >= requested * 0.25;
  const credit_ok = credit >= 650;
  const decision = affordability && credit_ok ? 'approved' : 'declined';
  const score = affordability && credit_ok ? 0.9 : 0.2;

  // If OpenAI configured, ask the model for a short justification as well
  let rationale = `Rule-based: affordability=${affordability}, credit_ok=${credit_ok}`;
  if (openaiClient) {
    try {
      const prompt = `You are an underwriting assistant. Given application data ${JSON.stringify(application)}, provide a short assessment of affordability (approved/declined), a numeric score 0-1, and a 1-2 sentence rationale.`;
      const res = await openaiClient.createChatCompletion({
        model: OPENAI_MODEL,
        messages: [{ role: 'user', content: prompt }],
        max_tokens: 200,
      });
      const text = res.data.choices?.[0]?.message?.content?.trim();
      if (text) {
        rationale = text;
      }
    } catch (e) {
      console.warn('OpenAI underwriting call failed, using fallback:', e.message);
    }
  }

  return { decision, score, rationale };
}

module.exports = { assess };
