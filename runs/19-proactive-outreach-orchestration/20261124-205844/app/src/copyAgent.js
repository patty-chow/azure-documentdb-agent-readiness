const { OpenAI } = require('openai');
const { v4: uuidv4 } = require('uuid');
require('dotenv').config();

const OPENAI_KEY = process.env.OPENAI_API_KEY;
let openai;
if (OPENAI_KEY) {
  openai = new OpenAI({ apiKey: OPENAI_KEY });
}

async function generateMessage(customer, event) {
  if (!OPENAI_KEY) {
    // fallback deterministic template for offline/demo mode
    return `Hi ${customer.name.split(' ')[0]}, we noticed a ${event.type.replace('_',' ')} — we'd love to help. Reply to this message or visit your account to take action.`;
  }

  // Use a simple prompt template. In a production LangChain pipeline, you'd
  // compose chains, tools, and prompt templates more fully.
  const model = process.env.MODEL_NAME || 'gpt-4o-mini';
  const prompt = `You are a polite marketing assistant. Given the customer and event, produce a short personalized outreach message (1-3 sentences) tailored to the customer's profile and preferred channel.\n\nCustomer: ${JSON.stringify(customer)}\nEvent: ${JSON.stringify(event)}\n\nMessage:`;

  const resp = await openai.chat.completions.create({
    model,
    messages: [{ role: 'system', content: 'You are a helpful assistant.' }, { role: 'user', content: prompt }],
    max_tokens: 200,
    temperature: 0.7,
  });

  const message = resp.choices?.[0]?.message?.content?.trim();
  return message || '';
}

module.exports = { generateMessage };
