import dotenv from 'dotenv';
dotenv.config();
import OpenAI from 'openai';

export async function generateRecoveryMessage(cart, customer) {
  const openaiKey = process.env.OPENAI_API_KEY;
  if (!openaiKey) {
    throw new Error('OPENAI_API_KEY not set');
  }
  const client = new OpenAI({ apiKey: openaiKey });

  const prompt = `You are a friendly e-commerce retention assistant.\nCustomer name: ${customer.name}\nCart total: $${cart.total}\nItems: ${cart.items.map(i => `${i.qty}x ${i.name}`).join(', ')}\nGoal: write a short, persuasive, personal message encouraging purchase, including a small incentive (e.g., 10% off) and clear CTA. Keep it under 120 words.`;
  try {
    const resp = await client.chat.completions.create({
      model: 'gpt-3.5-turbo',
      messages: [{ role: 'system', content: 'You are a helpful assistant.' }, { role: 'user', content: prompt }],
      max_tokens: 200,
      temperature: 0.7
    });
    const text = resp.choices?.[0]?.message?.content?.trim();
    return text || `Hi ${customer.name}, we noticed you left items in your cart. Come back to complete your purchase!`;
  } catch (e) {
    throw e;
  }
}
