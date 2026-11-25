import dotenv from 'dotenv';
dotenv.config();

const OPENAI_KEY = process.env.OPENAI_API_KEY;
let useOpenAI = !!OPENAI_KEY;

// We prefer to use LangChain + OpenAI when available. To avoid making the
// sample fail when users don't have keys, fall back to a deterministic
// template.

export async function generateMessage({ customer, cart }) {
  // customer: { _id, name, email, phone, preferredChannel }
  // cart: { _id, items, total, lastUpdated }
  if (!useOpenAI) {
    // simple template
    const name = customer?.name || 'customer';
    const itemCount = (cart.items || []).length;
    return `Hi ${name}, we noticed you left ${itemCount} item(s) in your cart. Come back to complete your purchase!`; 
  }

  // Use LangChain/OpenAI if API key present. Import lazily to avoid hard
  // runtime dependency unless used.
  try {
    const { OpenAI } = await import('langchain/llms/openai');
    const client = new OpenAI({ openAIApiKey: OPENAI_KEY, temperature: 0.7 });
    const prompt = `Write a short, personalized cart-recovery message for ${customer.name || 'valued customer'}. They left ${(cart.items||[]).length} items in their cart with total ${cart.total || ''}. Keep it friendly and include a clear call to action.`;
    const resp = await client.call(prompt);
    return resp;
  } catch (err) {
    console.warn('OpenAI generation failed, falling back to template:', err.message);
    const name = customer?.name || 'customer';
    const itemCount = (cart.items || []).length;
    return `Hi ${name}, we noticed you left ${itemCount} item(s) in your cart. Come back to complete your purchase!`;
  }
}
