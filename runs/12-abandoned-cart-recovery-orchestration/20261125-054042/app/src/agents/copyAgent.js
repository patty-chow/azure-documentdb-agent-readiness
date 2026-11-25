// Simple copy-generation agent using LangChain + OpenAI
class CopyAgent {
  constructor() {
    this.model = null;
    this.init();
  }

  init() {
    try {
      // Lazy require so tests can mock this module without loading langchain
      const { OpenAI } = require('langchain/llms/openai');
      this.model = new OpenAI({
        openAIApiKey: process.env.OPENAI_API_KEY,
        modelName: process.env.OPENAI_MODEL || 'gpt-3.5-turbo',
        temperature: 0.7,
      });
    } catch (err) {
      // In test or when langchain isn't installed/available, fall back to a noop model
      this.model = {
        call: async (prompt) => `SIMULATED: ${prompt.slice(0, 200)}`,
      };
    }
  }

  async generateMessage(cart, customer) {
    const items = (cart.items || []).map(i => `${i.name} (x${i.qty})`).join(', ');
    const prompt = `You are a friendly e-commerce recovery assistant. Write a short (1-3 sentence) personalised message to ${customer.name} to recover their cart. The cart contains: ${items}. Offer a gentle reminder and a single CTA. Use the customer's first name only.`;
    const res = await this.model.call(prompt);
    return res;
  }
}

module.exports = CopyAgent;
