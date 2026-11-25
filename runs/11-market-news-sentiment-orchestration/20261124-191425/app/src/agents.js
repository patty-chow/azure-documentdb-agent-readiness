const { OpenAI } = require('openai');
const fetch = require('cross-fetch');
const dotenv = require('dotenv');
dotenv.config();

const OPENAI_API_KEY = process.env.OPENAI_API_KEY;
const hasOpenAI = Boolean(OPENAI_API_KEY);
let client = null;
if (hasOpenAI) {
  client = new OpenAI({ apiKey: OPENAI_API_KEY });
} else {
  console.warn('OPENAI_API_KEY not set; using heuristic fallback for sentiment/ticker extraction in demo.');
}

// build system/user prompt
function buildPrompt(headline) {
  return `You are a financial text analyzer. Given a news headline, reply ONLY with a JSON object with the following fields:\n- sentiment_score: a number between -1 (very negative) and 1 (very positive)\n- tickers: an array of uppercase stock ticker symbols mentioned in the headline (if none, return empty array)\nExample output: {"sentiment_score":0.2,"tickers":["AAPL"]}\n\nHeadline: "${headline.replace(/\"/g,'\\"')}"`;
}

function heuristicAnalyze(headline) {
  // sentiment: naive polarity based on words
  const neg = ['falls','fall','drops','plunge','weak','decline','loss','cut','sink','slump','down'];
  const pos = ['rises','rise','gains','gain','surge','beats','strong','up','soars','jump'];
  const hl = headline.toLowerCase();
  let score = 0;
  for (const w of neg) if (hl.includes(w)) score -= 0.5;
  for (const w of pos) if (hl.includes(w)) score += 0.5;
  score = Math.max(-1, Math.min(1, score));
  // tickers: uppercase words of 1-5 letters, or $TICKER style
  const tickers = [];
  const dollarMatches = Array.from(headline.matchAll(/\$([A-Za-z]{1,5})/g)).map(m => m[1].toUpperCase());
  for (const t of dollarMatches) if (!tickers.includes(t)) tickers.push(t);
  const wordMatches = Array.from(headline.matchAll(/\b([A-Z]{2,5})\b/g)).map(m => m[1]);
  for (const t of wordMatches) if (!tickers.includes(t)) tickers.push(t);
  return { sentiment_score: score, tickers };
}

async function analyzeHeadline(headline) {
  if (!hasOpenAI) return heuristicAnalyze(headline);
  const prompt = buildPrompt(headline);
  try {
    const resp = await client.chat.completions.create({
      model: 'gpt-4o-mini',
      messages: [{ role: 'user', content: prompt }],
      temperature: 0
    });
    const text = resp.choices?.[0]?.message?.content || '';
    let out = { sentiment_score: 0, tickers: [] };
    try {
      const jsonStart = text.indexOf('{');
      const jsonText = text.slice(jsonStart);
      out = JSON.parse(jsonText);
    } catch (e) {
      const scoreMatch = text.match(/-?\d+(?:\.\d+)?/);
      if (scoreMatch) out.sentiment_score = parseFloat(scoreMatch[0]);
      const tickers = text.match(/\b[A-Z]{1,5}\b/g);
      if (tickers) out.tickers = [...new Set(tickers)];
    }
    out.sentiment_score = Math.max(-1, Math.min(1, Number(out.sentiment_score) || 0));
    out.tickers = Array.isArray(out.tickers) ? out.tickers.map(t => t.toUpperCase()) : [];
    return out;
  } catch (e) {
    console.warn('OpenAI call failed; falling back to heuristic:', e.message);
    return heuristicAnalyze(headline);
  }
}

async function notifyWebhook(payload) {
  const url = process.env.WEBHOOK_URL;
  if (!url) return console.log('No WEBHOOK_URL configured; skipping webhook POST.');
  const token = process.env.WEBHOOK_TOKEN;
  const headers = { 'Content-Type': 'application/json' };
  if (token) headers['Authorization'] = `Bearer ${token}`;
  try {
    const resp = await fetch(url, { method: 'POST', headers, body: JSON.stringify(payload) });
    console.log('Webhook POST status', resp.status);
  } catch (e) {
    console.error('Webhook POST failed', e.message);
  }
}

module.exports = { analyzeHeadline, notifyWebhook };
