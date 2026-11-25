// CLI entrypoint to score a lead and write score + rationale back to leads collection
// Usage: node src/scoreLead.js --leadId=lead-1

require('dotenv').config();
const minimist = require('minimist');
const { getDb, getClient } = require('./db');
const { OpenAI } = require('openai');

async function computeHeuristicScore({ activities, signals, company }) {
  // Simple deterministic heuristic used when OPENAI_API_KEY is not set or for quick runs
  const activityCount = activities.length;
  const avgSignal = signals.length ? signals.reduce((s,a)=>s+a.score,0)/signals.length : 0;
  let score = Math.round(Math.min(100, activityCount * 10 + avgSignal * 80));
  let rationale = `Heuristic score: ${activityCount} recent activities and average signal ${avgSignal.toFixed(2)} produced score ${score}.`;
  return { score, rationale };
}

async function computeOpenAIScore({ lead, activities, signals, company }) {
  const apiKey = process.env.OPENAI_API_KEY;
  if (!apiKey) {
    return computeHeuristicScore({ activities, signals, company });
  }
  const client = new OpenAI({ apiKey });
  const chatModel = process.env.OPENAI_CHAT_MODEL || 'gpt-4o-mini';

  const prompt = `You are a lead scoring assistant. Given the lead: ${JSON.stringify(lead)}, company: ${JSON.stringify(company)}, activities: ${JSON.stringify(activities)}, signals: ${JSON.stringify(signals)}\n\nPlease reply with a JSON object with fields {"score": number between 0 and 100, "rationale": "one paragraph explaining the decision"}.`;

  const resp = await client.chat.completions.create({
    model: chatModel,
    messages: [{ role: 'user', content: prompt }],
    max_tokens: 300
  });
  const text = resp.choices?.[0]?.message?.content?.trim();
  try {
    const parsed = JSON.parse(text);
    return { score: Math.round(parsed.score), rationale: parsed.rationale };
  } catch (e) {
    // fallback: use heuristic
    return computeHeuristicScore({ activities, signals, company });
  }
}

async function scoreLead(leadId) {
  const db = await getDb();
  const leads = db.collection('leads');
  const activitiesCol = db.collection('activities');
  const signalsCol = db.collection('engagement_signals');
  const companies = db.collection('companies');

  const lead = await leads.findOne({ _id: leadId }) || await leads.findOne({ leadId });
  if (!lead) throw new Error('Lead not found: ' + leadId);

  const activities = await activitiesCol.find({ leadId: leadId }).sort({ timestamp: -1 }).limit(50).toArray();
  const signals = await signalsCol.find({ leadId: leadId }).toArray();
  const company = lead.companyId ? await companies.findOne({ companyId: lead.companyId }) : null;

  let result;
  if (process.env.OPENAI_API_KEY) {
    result = await computeOpenAIScore({ lead, activities, signals, company });
  } else {
    result = await computeHeuristicScore({ activities, signals, company });
  }

  // write back to lead document
  await leads.updateOne({ _id: lead._id }, { $set: { score: result.score, score_rationale: result.rationale } });

  // return the updated lead
  const updated = await leads.findOne({ _id: lead._id });
  return updated;
}

if (require.main === module) {
  const argv = minimist(process.argv.slice(2));
  const leadId = argv.leadId || argv.leadid || argv.id;
  if (!leadId) {
    console.error('Usage: node src/scoreLead.js --leadId=lead-1');
    process.exit(1);
  }
  scoreLead(leadId).then(l => {
    console.log('Lead updated:', l);
    return getClient().close();
  }).catch(err => {
    console.error('Error scoring lead:', err);
    process.exit(1);
  });
}

module.exports = { scoreLead };
