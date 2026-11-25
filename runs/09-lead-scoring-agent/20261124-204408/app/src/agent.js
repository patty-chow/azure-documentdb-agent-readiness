require('dotenv').config();
const { getDb, getClient } = require('./db');
const OpenAI = require('openai');

const MODEL = process.env.OPENAI_MODEL || 'gpt-3.5-turbo';

async function fetchLeadContext(leadId) {
  const db = await getDb();
  const leads = db.collection('leads');
  const activities = db.collection('activities');
  const companies = db.collection('companies');
  const signals = db.collection('engagement_signals');

  const lead = await leads.findOne({ leadId });
  if (!lead) throw new Error(`Lead not found: ${leadId}`);
  const company = lead.companyId ? await companies.findOne({ companyId: lead.companyId }) : null;
  const recentActivities = await activities.find({ leadId }).sort({ timestamp: -1 }).limit(20).toArray();
  const engagement = await signals.find({ leadId }).toArray();
  return { lead, company, recentActivities, engagement };
}

function buildPrompt(context) {
  const { lead, company, recentActivities, engagement } = context;
  const lines = [];
  lines.push(`You are a sales-scoring assistant. Produce a numeric score 0-100 (higher means more likely to convert) and one short paragraph rationale. Return ONLY a JSON object with keys: score (integer) and rationale (string).`);
  lines.push(`Lead: ${lead.name} (${lead.email}), leadId=${lead.leadId}`);
  if (company) lines.push(`Company: ${company.name}, industry=${company.industry}, size=${company.size}`);
  lines.push('Recent activities:');
  for (const a of recentActivities.slice(0, 10)) {
    lines.push(` - ${a.type} @ ${new Date(a.timestamp).toISOString()}: ${a.details || ''}`);
  }
  lines.push('Engagement signals:');
  for (const s of engagement) {
    lines.push(` - ${s.signal}: ${s.value}`);
  }
  lines.push('Give a single JSON object as described.');
  return lines.join('\n');
}

async function callLLM(prompt) {
  if (!process.env.OPENAI_API_KEY) throw new Error('OPENAI_API_KEY is required to call the LLM');
  const openai = new OpenAI({ apiKey: process.env.OPENAI_API_KEY });
  const resp = await openai.chat.completions.create({
    model: MODEL,
    messages: [{ role: 'user', content: prompt }],
    max_tokens: 400
  });
  const content = resp.choices?.[0]?.message?.content;
  if (!content) throw new Error('LLM returned no content');
  return content;
}

function parseLLMOutput(text) {
  // try to find JSON in the output
  const start = text.indexOf('{');
  const end = text.lastIndexOf('}');
  if (start === -1 || end === -1) throw new Error('No JSON object found in LLM output');
  const jsonText = text.slice(start, end + 1);
  const obj = JSON.parse(jsonText);
  if (typeof obj.score !== 'number') throw new Error('Parsed JSON missing numeric score');
  return obj;
}

async function scoreLead(leadId) {
  const context = await fetchLeadContext(leadId);
  const prompt = buildPrompt(context);
  const llmText = await callLLM(prompt);
  const parsed = parseLLMOutput(llmText);

  // clamp score
  let score = Math.max(0, Math.min(100, Math.round(parsed.score)));
  const rationale = parsed.rationale || '';

  const db = await getDb();
  const leads = db.collection('leads');
  await leads.updateOne({ leadId }, { $set: { score, score_rationale: rationale, scoredAt: new Date() } });
  return { score, rationale };
}

module.exports = { scoreLead, fetchLeadContext, buildPrompt };
