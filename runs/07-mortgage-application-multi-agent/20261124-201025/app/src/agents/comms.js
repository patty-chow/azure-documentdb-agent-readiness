// Comms agent: drafts a decision letter. LLM optional, otherwise template-based
const { Configuration, OpenAIApi } = require('openai');
require('dotenv').config();

const OPENAI_API_KEY = process.env.OPENAI_API_KEY;
const OPENAI_MODEL = process.env.OPENAI_MODEL || 'gpt-4o-mini';

let openaiClient;
if (OPENAI_API_KEY) {
  const configuration = new Configuration({ apiKey: OPENAI_API_KEY });
  openaiClient = new OpenAIApi(configuration);
}

async function draft(application, underwriting, compliance) {
  const applicant = application.name || 'Applicant';
  const decision = underwriting.decision === 'approved' ? 'APPROVED' : 'DECLINED';
  const template = `Dear ${applicant},\n\nWe have completed our review of your mortgage application (ID: ${application.applicationId}). Decision: ${decision}.\n\nUnderwriting notes: ${underwriting.rationale}\nCompliance notes: ${compliance.rationale}\n\nSincerely,\nSample Bank`;

  if (openaiClient) {
    try {
      const prompt = `Draft a polite decision letter for application: ${JSON.stringify({ application, underwriting, compliance })}`;
      const res = await openaiClient.createChatCompletion({
        model: OPENAI_MODEL,
        messages: [{ role: 'user', content: prompt }],
        max_tokens: 300,
      });
      const text = res.data.choices?.[0]?.message?.content?.trim();
      if (text) return text;
    } catch (e) {
      console.warn('OpenAI comms call failed, using fallback template:', e.message);
    }
  }

  return template;
}

module.exports = { draft };
