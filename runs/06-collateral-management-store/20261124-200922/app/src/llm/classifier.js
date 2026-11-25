const { OpenAIApi, Configuration } = require('openai');

let openai = null;
function getClient() {
  if (openai) return openai;
  const key = process.env.OPENAI_API_KEY;
  if (!key) return null;
  const cfg = new Configuration({ apiKey: key });
  openai = new OpenAIApi(cfg);
  return openai;
}

async function classifyAsset(asset) {
  // If disabled or no key present, return a light heuristic
  if (process.env.DISABLE_LLM === 'true') {
    return { assetType: (asset.metadata && asset.metadata.category) || 'unknown', eligibilityTier: 'unknown' };
  }
  const client = getClient();
  if (!client) {
    // No key configured; fallback heuristic
    return { assetType: (asset.metadata && asset.metadata.category) || 'unknown', eligibilityTier: 'unknown' };
  }

  const model = process.env.MODEL_NAME || 'gpt-4o-mini';
  // Build a short prompt for classification
  const prompt = `You are a short classifier. Given a JSON asset with fields assetId, metadata and valuation, return a JSON object with assetType and eligibilityTier. EligibilityTier must be one of: high, medium, low, ineligible. AssetType should be a concise label (e.g., 'residential_mortgage', 'commercial_real_estate', 'cash', 'securities').\n\nAsset: ${JSON.stringify(asset)}\n\nReturn just JSON.`;

  try {
    const resp = await client.createChatCompletion({
      model,
      messages: [{ role: 'system', content: 'You are a concise classifier.' }, { role: 'user', content: prompt }],
      max_tokens: 128,
      temperature: 0
    });
    const text = resp.data.choices?.[0]?.message?.content?.trim();
    // Try parse JSON from response
    try {
      const parsed = JSON.parse(text);
      return {
        assetType: parsed.assetType || 'unknown',
        eligibilityTier: parsed.eligibilityTier || 'unknown'
      };
    } catch (e) {
      // fallback heuristics
      return { assetType: (asset.metadata && asset.metadata.category) || 'unknown', eligibilityTier: 'unknown' };
    }
  } catch (err) {
    console.error('LLM classification failed:', err?.message || err);
    return { assetType: (asset.metadata && asset.metadata.category) || 'unknown', eligibilityTier: 'unknown' };
  }
}

module.exports = { classifyAsset };
