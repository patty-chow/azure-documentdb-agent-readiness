const { OpenAI } = require('openai');
const dotenv = require('dotenv');
dotenv.config();

const openaiKey = process.env.OPENAI_API_KEY;
const modelName = process.env.OPENAI_MODEL || 'gpt-4o-mini';

let client = null;
if (openaiKey) {
  client = new OpenAI({ apiKey: openaiKey });
}

// Simple copy generator that calls OpenAI Chat Completions to make a short personalized message
async function generateRecoveryMessage({ customer, cart }) {
  if (!client) {
    // fallback: non-LLM stubbed copy
    return `Hi ${customer.name}, we noticed items left in your cart (${cart.items.map(i=>i.name).join(', ')}). Come back to complete your purchase!`;
  }

  const itemsList = cart.items.map(i => `- ${i.qty} x ${i.name} (${i.sku})`).join('\n');
  const prompt = `You are a friendly customer-recovery assistant. Write a short (<= 2 sentences) personalized message to ${customer.name} encouraging them to return and complete their purchase. Include the items:
${itemsList}
Keep the tone friendly and include a small incentive: a 10% off mention.`;

  const resp = await client.chat.completions.create({
    model: modelName,
    messages: [{ role: 'user', content: prompt }],
    max_tokens: 200,
    temperature: 0.7
  });

  // OpenAI SDK chat completion response parsing
  const content = resp.choices && resp.choices[0] && resp.choices[0].message && resp.choices[0].message.content;
  return content ? content.trim() : `Hi ${customer.name}, we noticed items left in your cart. Come back to complete your purchase!`;
}

module.exports = { generateRecoveryMessage };
