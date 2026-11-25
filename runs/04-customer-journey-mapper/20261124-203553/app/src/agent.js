require('dotenv').config();
const { OpenAIApi, Configuration, OpenAI } = (() => {
  try {
    // attempt to require openai in a way compatible with older/newer SDKs
    const mod = require('openai');
    // prefer the modern default export if present
    return { OpenAIApi: mod.OpenAIApi, Configuration: mod.Configuration, OpenAI: mod.default || mod.OpenAI };
  } catch (err) {
    return {};
  }
})();

function buildPrompt(journey) {
  // Build a structured timeline representation for the model.
  const lines = [];
  lines.push(`Customer ID: ${journey.customerId}`);
  lines.push('Structured timeline:');
  for (const ev of journey.timeline) {
    const t = ev.timestamp ? new Date(ev.timestamp).toISOString() : 'unknown';
    lines.push(`- ${t} | channel=${ev.channel || 'unknown'} | type=${ev.eventType || 'unknown'} | metadata=${JSON.stringify(ev.metadata || {})}`);
  }
  lines.push('\nGroupings by channel:');
  for (const [ch, events] of Object.entries(journey.byChannel)) {
    lines.push(`- ${ch}: ${events.length} events (first=${events[0] ? new Date(events[0].timestamp).toISOString() : 'n/a'}, last=${events[events.length-1] ? new Date(events[events.length-1].timestamp).toISOString() : 'n/a'})`);
  }

  lines.push('\nTask:');
  lines.push('Please produce a JSON object with two top-level keys: "summary" (a plain-language paragraph summarizing the customer journey and highlighting key inflection points), and "inflectionPoints" (an array of objects each with keys: "time", "description", "whyImportant").');
  lines.push('Be concise. Use ISO timestamps for times. If you detect gaps > 7 days between consecutive events, treat them as possible inflection points. If channel switches or eventTypes like "purchase", "cancel", "support_contact" occur, highlight them. Return only valid JSON.');

  return lines.join('\n');
}

async function summarizeJourney(journey) {
  const prompt = buildPrompt(journey);
  const model = process.env.MODEL_NAME || 'gpt-4o-mini';

  // Instantiate OpenAI client at call time to avoid import-time errors in tests
  let client = null;
  if (process.env.OPENAI_API_KEY) {
    if (OpenAI) {
      client = new OpenAI({ apiKey: process.env.OPENAI_API_KEY });
    } else if (Configuration && OpenAIApi) {
      const configuration = new Configuration({ apiKey: process.env.OPENAI_API_KEY });
      client = new OpenAIApi(configuration);
    } else {
      throw new Error('OpenAI client library not available');
    }
  } else {
    throw new Error('OPENAI_API_KEY not set in environment; cannot call LLM');
  }

  // Call Chat Completion depending on client shape
  let text = '';
  if (client.createChatCompletion) {
    const resp = await client.createChatCompletion({ model, messages: [ { role: 'system', content: 'You are a helpful assistant that summarizes customer timelines and detects inflection points.' }, { role: 'user', content: prompt } ], max_tokens: 800 });
    text = resp.data.choices && resp.data.choices[0] && resp.data.choices[0].message ? resp.data.choices[0].message.content : null;
  } else if (client.chat && client.chat.completions.create) {
    const resp = await client.chat.completions.create({ model, messages: [ { role: 'system', content: 'You are a helpful assistant that summarizes customer timelines and detects inflection points.' }, { role: 'user', content: prompt } ], max_tokens: 800 });
    text = resp.choices && resp.choices[0] && resp.choices[0].message ? resp.choices[0].message.content : null;
  } else {
    throw new Error('Unsupported OpenAI client shape');
  }

  let parsed = null;
  try {
    parsed = JSON.parse(text);
  } catch (err) {
    // If the model did not return strict JSON, wrap the text into summary key
    parsed = { summary: text, inflectionPoints: [] };
  }
  return parsed;
}

module.exports = { buildPrompt, summarizeJourney };
