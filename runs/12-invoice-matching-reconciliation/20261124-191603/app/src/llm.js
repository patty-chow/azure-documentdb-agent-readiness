import dotenv from 'dotenv';
import OpenAI from 'openai';

dotenv.config();
const openaiKey = process.env.OPENAI_API_KEY;
const embeddingModel = process.env.OPENAI_EMBEDDING_MODEL || 'text-embedding-3-small';
const extractModel = process.env.OPENAI_EXTRACT_MODEL || 'gpt-4o-mini';

let client = null;
if (openaiKey) {
  client = new OpenAI({ apiKey: openaiKey });
}

export async function extractFieldsFallback(text) {
  // Very simple parser: look for amounts and vendor tokens
  const vendorMatch = text.match(/vendor[:\s]+([\w\s\.\-,&]+)/i);
  const amountMatch = text.match(/\$?([0-9]+(?:\.[0-9]{1,2})?)/);
  return {
    vendorName: vendorMatch ? vendorMatch[1].trim() : undefined,
    totalAmount: amountMatch ? parseFloat(amountMatch[1]) : undefined
  };
}

export async function extractFieldsLLM(text) {
  if (!client) return extractFieldsFallback(text);
  const prompt = `Extract structured fields from the invoice text. Return JSON with keys: vendorName, totalAmount, invoiceNumber, invoiceDate (YYYY-MM-DD if present).\n\nInvoice text:\n${text}`;
  const resp = await client.chat.completions.create({
    model: extractModel,
    messages: [{ role: 'user', content: prompt }],
    max_tokens: 400
  });
  const content = resp.choices?.[0]?.message?.content || '';
  try {
    const jsonStart = content.indexOf('{');
    const json = JSON.parse(content.slice(jsonStart));
    return json;
  } catch (e) {
    // fallback
    return extractFieldsFallback(text);
  }
}

export async function embedText(text) {
  if (!client) return null;
  const resp = await client.embeddings.create({ model: embeddingModel, input: text });
  return resp.data?.[0]?.embedding || null;
}
