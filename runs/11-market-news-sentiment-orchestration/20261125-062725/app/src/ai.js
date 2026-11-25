require('dotenv').config();
const { OpenAI } = require('openai');

const openaiKey = process.env.OPENAI_API_KEY;
let openaiClient = null;
if(openaiKey){
  openaiClient = new OpenAI({ apiKey: openaiKey });
}

async function analyzeHeadlineLLM(headline){
  // If no OpenAI key, fallback to simple rule-based sentiment and ticker extraction
  if(!openaiClient){
    const text = headline.toLowerCase();
    let sentiment = 0;
    if(text.includes('beat') || text.includes('record') || text.includes('jump') || text.includes('grows') || text.includes('rally') || text.includes('rebounds')) sentiment = 1;
    if(text.includes('tumbles') || text.includes('file') || text.includes('bankrupt') || text.includes('fine') || text.includes('delay') || text.includes('struggles')) sentiment = -1;
    // crude ticker extraction: uppercase words of length 1-5
    const tickers = (headline.match(/\b[A-Z]{1,5}\b/g) || []).filter(t=>t.length<=5);
    return { sentiment, tickers };
  }

  // Use OpenAI completions to extract sentiment and tickers as JSON
  const prompt = `Analyze the sentiment of this headline and extract any stock tickers mentioned. Return only a JSON object with keys: sentiment (number -1..1), tickers (array of uppercase strings).\n\nHeadline: "${headline.replace(/\"/g,'\\\"')}"`;
  try{
    const completion = await openaiClient.chat.completions.create({
      model: 'gpt-4o-mini',
      messages: [{role:'user', content: prompt}],
      max_tokens: 200
    });
    const text = completion.choices?.[0]?.message?.content || completion.choices?.[0]?.text || '';
    // try to parse JSON
    const jsonStart = text.indexOf('{');
    const jsonText = jsonStart>=0 ? text.slice(jsonStart) : text;
    const parsed = JSON.parse(jsonText);
    return { sentiment: parsed.sentiment ?? 0, tickers: parsed.tickers ?? [] };
  }catch(e){
    console.warn('LLM analysis failed, falling back to heuristics', e.message||e);
    // fallback heuristics
    const text = headline.toLowerCase();
    let sentiment = 0;
    if(text.includes('beat') || text.includes('record') || text.includes('jump') || text.includes('grows') || text.includes('rally') || text.includes('rebounds')) sentiment = 1;
    if(text.includes('tumbles') || text.includes('file') || text.includes('bankrupt') || text.includes('fine') || text.includes('delay') || text.includes('struggles')) sentiment = -1;
    const tickers = (headline.match(/\b[A-Z]{1,5}\b/g) || []).filter(t=>t.length<=5);
    return { sentiment, tickers };
  }
}

async function embedText(text){
  if(!openaiClient) return null;
  try{
    const res = await openaiClient.embeddings.create({ model: 'text-embedding-3-small', input: text });
    return res.data[0].embedding;
  }catch(e){
    console.warn('Embedding call failed:', e.message||e);
    return null;
  }
}

module.exports = { analyzeHeadlineLLM, embedText };
