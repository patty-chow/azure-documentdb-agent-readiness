require('dotenv').config();
const { OpenAI } = require('openai');

const openaiKey = process.env.OPENAI_API_KEY;
const client = openaiKey ? new OpenAI({ apiKey: openaiKey }) : null;

// Simple LangChain-style wrapper for extraction and embeddings (demo)
class LangChainAgent {
  constructor() {
    this.memory = {}; // in-memory session memory: { sessionId: { corrections: {invoiceNumber: matchedPoNumber} } }
  }

  getSession(sessionId) {
    if (!sessionId) sessionId = 'default';
    if (!this.memory[sessionId]) this.memory[sessionId] = { corrections: {} };
    return this.memory[sessionId];
  }

  addCorrection(sessionId, invoiceNumber, matchedPoNumber) {
    const s = this.getSession(sessionId);
    s.corrections[invoiceNumber] = matchedPoNumber;
  }

  // Extract invoice fields from free text using the LLM. Returns { vendorName, totalAmount }
  async extractInvoiceFields(text) {
    if (!client) {
      // heuristic fallback: look for numbers and a capitalized word for vendor
      const vendorMatch = text.match(/Vendor:\s*([A-Za-z0-9 &\-]+)/i);
      const amountMatch = text.match(/\$?([0-9]+(?:\.[0-9]{2})?)/);
      return { vendorName: vendorMatch ? vendorMatch[1].trim() : null, totalAmount: amountMatch ? parseFloat(amountMatch[1]) : null };
    }

    const prompt = `Extract the vendor name and the invoice total from the following invoice text in JSON as {"vendorName":"...","totalAmount":number}. If a value is missing, use null.\n\nInvoice:\n${text}`;

    const resp = await client.responses.create({
      model: 'gpt-4o-mini',
      input: prompt,
      max_output_tokens: 300
    });
    const out = (resp.output && resp.output[0] && resp.output[0].content) ? resp.output[0].content[0].text : null;
    try {
      const js = JSON.parse(out);
      return { vendorName: js.vendorName || null, totalAmount: js.totalAmount || null };
    } catch (e) {
      // best-effort parse numbers
      const amountMatch = out && out.match(/([0-9]+(?:\.[0-9]{2})?)/);
      return { vendorName: out ? out.trim().split('\n')[0] : null, totalAmount: amountMatch ? parseFloat(amountMatch[1]) : null };
    }
  }

  async embedText(text) {
    if (!client) return null;
    const resp = await client.embeddings.create({ model: 'text-embedding-3-small', input: text });
    return resp.data[0].embedding;
  }
}

module.exports = new LangChainAgent();
