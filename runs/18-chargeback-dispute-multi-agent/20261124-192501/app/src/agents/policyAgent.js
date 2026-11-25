const { OpenAI } = require('openai');
const dotenv = require('dotenv');
dotenv.config();

// Minimal policy agent: sends evidence to an LLM to get a recommendation
// This keeps the dependency surface small. In production you would use LangChain flows.

const openaiKey = process.env.OPENAI_API_KEY;
if (!openaiKey) {
  console.warn('OPENAI_API_KEY not set. Policy agent will fail if invoked without it.');
}

const client = openaiKey ? new OpenAI({ apiKey: openaiKey }) : null;

async function reasonPolicy(evidence) {
  // evidence: { claim, transactions, communications }
  const prompt = `You are a chargeback policy engine. Given the claim and evidence, reply with a JSON object {recommendation: "accept"|"reject", rationale: "..."}.

Claim: ${JSON.stringify(evidence.claim)}
Transactions: ${JSON.stringify(evidence.transactions)}
Communications: ${JSON.stringify(evidence.communications)}

Make a short recommendation.`;

  if (!client) {
    // Fallback deterministic heuristic when no LLM key is present
    const tx = evidence.transactions[0];
    const amount = tx?.amount || 0;
    const hasRefund = evidence.communications.some(c => c.text && c.text.toLowerCase().includes('refund'));
    const rec = (hasRefund || amount === 0) ? 'accept' : 'reject';
    return { recommendation: rec, rationale: 'Heuristic fallback: presence of refund request or zero amount' };
  }

  const resp = await client.responses.create({
    model: process.env.OPENAI_MODEL || 'gpt-4o-mini',
    input: prompt,
    max_output_tokens: 300
  });
  // Attempt to parse JSON from LLM output
  const text = Array.isArray(resp.output) ? resp.output.map(o => o.content).join('\n') : resp.outputText || '';
  try {
    const firstJson = text.match(/\{[\s\S]*\}/);
    if (firstJson) return JSON.parse(firstJson[0]);
  } catch (e) {
    // fall through
  }
  return { recommendation: 'reject', rationale: 'Could not parse LLM response' };
}

// Additional exported heuristic function used by unit tests
function evaluateEvidence(evidence) {
  const amount = evidence.transaction?.amount ?? 0;
  if (amount <= 100) return { decision: 'accept', reason: 'Small amount heuristic' };
  return { decision: 'reject', reason: 'Large amount heuristic' };
}

module.exports = { reasonPolicy, evaluateEvidence };
