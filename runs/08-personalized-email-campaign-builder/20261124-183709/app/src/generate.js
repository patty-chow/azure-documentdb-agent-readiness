const { getDb, clientPromise } = require('./client');
const dotenv = require('dotenv');
dotenv.config();
const yargs = require('yargs/yargs');
const { hideBin } = require('yargs/helpers');

const argv = yargs(hideBin(process.argv)).option('segmentId', { type: 'string', demandOption: true }).argv;
const OPENAI_KEY = process.env.OPENAI_API_KEY;
const OPENAI_MODEL = process.env.OPENAI_MODEL || 'gpt-4o-mini';
const USE_OPENAI = process.env.USE_OPENAI === '1';

async function callOpenAI(prompt) {
  if (!OPENAI_KEY || !USE_OPENAI) return null;
  const OpenAI = require('openai').default;
  const client = new OpenAI({ apiKey: OPENAI_KEY });

  // set a timeout via AbortController to avoid hanging forever
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 15000);

  try {
    const resp = await client.chat.completions.create({
      model: OPENAI_MODEL,
      messages: [{ role: 'user', content: prompt }],
      max_tokens: 500,
      temperature: 0.8,
      signal: controller.signal,
    });
    return resp.choices && resp.choices[0] && resp.choices[0].message && resp.choices[0].message.content;
  } catch (err) {
    console.warn('OpenAI call failed or timed out, falling back to deterministic generator:', err && err.message);
    return null;
  } finally {
    clearTimeout(timeout);
  }
}

function fallbackGeneration(segment) {
  const name = segment.name || segment.segmentId;
  const recent = (segment.purchase_history || []).slice(-1)[0];
  const subject = `Special picks for ${name}: ${recent ? recent.name : 'Our favorites'}`;
  const body = `Hi ${name},\n\nWe thought you might love ${recent ? recent.name : 'these items'} based on your recent purchases. Enjoy personalized discounts tailored to your preferences (${Object.values(segment.preferences || {}).join(', ')}).\n\nBest,\nYour Team`;
  return { subject, body, raw: `FALLBACK: subject=${subject}\nbody=${body}` };
}

async function generateForSegment(segmentId) {
  await clientPromise;
  const db = getDb();
  const segments = db.collection('segments');
  const campaigns = db.collection('campaigns');

  const segment = await segments.findOne({ segmentId });
  if (!segment) {
    console.error('Segment not found:', segmentId);
    process.exit(2);
  }

  // Build prompt with context engineering: inject purchase history and preferences
  const prompt = `You are a marketing copywriter. Given the following customer segment profile, craft a short email subject line (<= 70 chars) and a 2-4 paragraph email body aimed at converting that segment. Return ONLY a JSON object with keys: subject, body.\n\nSEGMENT_PROFILE:\n${JSON.stringify({ segmentId: segment.segmentId, name: segment.name, purchase_history: segment.purchase_history, preferences: segment.preferences }, null, 2)}\n\nRequirements:\n- Subject should be catchy and reflect the segment's preferences and purchase history.\n- Body should include a personalized line referencing a recent purchase if present, an offer or call to action, and a tone aligned with preferences.tone.\n- Output valid JSON only.`;

  let generated = null;
  const raw = await callOpenAI(prompt);
  if (raw) {
    // try to parse JSON from model
    try {
      const parsed = JSON.parse(raw);
      generated = { subject: parsed.subject, body: parsed.body, rawOutput: raw };
    } catch (e) {
      // fallback: wrap raw into rawOutput and make a simple extraction
      generated = { subject: null, body: null, rawOutput: raw };
    }
  } else {
    generated = fallbackGeneration(segment);
  }

  const doc = {
    segmentId: segment.segmentId,
    segmentName: segment.name,
    subject: generated.subject || '',
    body: generated.body || generated.raw || '',
    rawOutput: generated.rawOutput || generated.raw || raw || '',
    createdAt: new Date(),
  };

  const res = await campaigns.insertOne(doc);
  console.log('Inserted campaign id', res.insertedId);
}

generateForSegment(argv.segmentId).catch(err => {
  console.error(err);
  process.exit(1);
});
