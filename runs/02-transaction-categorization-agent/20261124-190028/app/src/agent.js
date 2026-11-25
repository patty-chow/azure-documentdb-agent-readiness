const { OpenAI } = require('langchain/llms/openai');
const dotenv = require('dotenv');
const TAXONOMY = [
  'Food',
  'Travel',
  'Utilities',
  'Entertainment',
  'Income',
  'Healthcare',
  'Shopping',
  'Other'
];

dotenv.config();

if (!process.env.OPENAI_API_KEY) {
  throw new Error('OPENAI_API_KEY must be set in environment');
}

// Create a LangChain-backed LLM (wrapper around OpenAI)
const llm = new OpenAI({ apiKey: process.env.OPENAI_API_KEY, modelName: 'gpt-3.5-turbo' });

async function categorizeTransaction(tx) {
  // Prompt engineering: give taxonomy, few-shot examples, and explicit instruction
  const prompt = `You are a transaction categorization assistant. Choose ONE category from this fixed taxonomy: ${TAXONOMY.join(', ')}.\n\n` +
    `Return exactly the single category label only (no extra text). If the merchant or amount suggests multiple possibilities, pick the best fitting category.\n\n` +
    `Example 1:\nMerchant: "Starbucks"\nAmount: 5.50\nCategory: Food\n\n` +
    `Example 2:\nMerchant: "Delta Airlines"\nAmount: 450.00\nCategory: Travel\n\n` +
    `Now categorize this transaction:\nMerchant: "${tx.merchant || ''}"\nAmount: ${tx.amount}\nDate: ${tx.date ? tx.date.toISOString() : ''}\nCategory:`;

  const resp = await llm.call(prompt);
  const text = (resp || '').trim();
  // Normalize and map to taxonomy
  const normalized = text.replace(/[^A-Za-z]/g, '').toLowerCase();
  const found = TAXONOMY.find(c => c.toLowerCase().replace(/[^a-z]/g, '') === normalized);
  if (found) return found;
  // Try fuzzy match by startsWith
  const startMatch = TAXONOMY.find(c => text.toLowerCase().includes(c.toLowerCase()));
  if (startMatch) return startMatch;
  return 'Other';
}

module.exports = { categorizeTransaction, TAXONOMY };
