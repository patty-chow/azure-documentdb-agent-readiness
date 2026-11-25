const { OpenAI } = require('openai');
const mockPolicy = async (order, reason) => {
  const eligible = (order.total || 0) <= 100;
  return {
    eligible,
    reasons: eligible ? ['Within 30-day window', 'No damages reported'] : ['Past 30-day window or high value requires manual review']
  };
};

const mockRefund = async (order, policyResult) => {
  if (!policyResult.eligible) return { amount: 0, breakdown: [] };
  const amount = Math.round((order.total || 0) * 100) / 100;
  return { amount, breakdown: [{ reason: 'full refund', amount }] };
};

const mockComms = async (order, refundResult) => {
  if (refundResult.amount === 0) {
    return { subject: `Return request for ${order.orderId} - Rejected`, body: `Dear customer, your return request was rejected. Reason: ${refundResult.reason || 'policy'}` };
  }
  return { subject: `Return approved for ${order.orderId}`, body: `Dear customer, we approved your return. Refund: ${refundResult.amount} ${order.currency || 'USD'}` };
};

function useMock() {
  return !process.env.OPENAI_API_KEY;
}

async function callOpenAI(prompt, systemInstruction) {
  const client = new OpenAI({ apiKey: process.env.OPENAI_API_KEY });
  const model = process.env.OPENAI_MODEL || 'gpt-4o-mini';
  const messages = [];
  if (systemInstruction) messages.push({ role: 'system', content: systemInstruction });
  messages.push({ role: 'user', content: prompt });
  const resp = await client.chat.completions.create({ model, messages, max_tokens: 800 });
  // openai response shape: choices[0].message.content
  const text = resp.choices && resp.choices[0] && resp.choices[0].message && resp.choices[0].message.content;
  return text;
}

async function policyAgent(order, reason) {
  if (useMock()) return mockPolicy(order, reason);
  const system = 'You are a returns policy evaluation agent. Answer with JSON: { eligible: boolean, reasons: [string] }';
  const prompt = `Order: ${JSON.stringify(order)}\nReason: ${reason}\nReturn a JSON object with fields 'eligible' and 'reasons'.`;
  const text = await callOpenAI(prompt, system);
  try { return JSON.parse(text); } catch (e) { return { eligible: false, reasons: ['llm_parse_error'] }; }
}

async function refundAgent(order, policyResult) {
  if (useMock()) return mockRefund(order, policyResult);
  const system = 'You are a refund calculation agent. Answer with JSON: { amount: number, breakdown: [{reason:string, amount:number}], reason?: string }';
  const prompt = `Order: ${JSON.stringify(order)}\nPolicy: ${JSON.stringify(policyResult)}\nReturn a JSON refund result.`;
  const text = await callOpenAI(prompt, system);
  try { return JSON.parse(text); } catch (e) { return { amount: 0, breakdown: [], reason: 'llm_parse_error' }; }
}

async function commsAgent(order, refundResult) {
  if (useMock()) return mockComms(order, refundResult);
  const system = 'You are a communications agent. Return JSON: { subject: string, body: string }';
  const prompt = `Order: ${JSON.stringify(order)}\nRefund: ${JSON.stringify(refundResult)}\nProduce customer-facing subject and body JSON.`;
  const text = await callOpenAI(prompt, system);
  try { return JSON.parse(text); } catch (e) { return { subject: 'Issue processing return', body: 'We could not process your return at this time.' }; }
}

module.exports = { policyAgent, refundAgent, commsAgent, useMock };
