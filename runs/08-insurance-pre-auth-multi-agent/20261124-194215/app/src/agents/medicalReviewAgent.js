require('dotenv').config();
const { getDb } = require('../db');
const OpenAI = require('openai');

const openaiKey = process.env.OPENAI_API_KEY;
const chatModel = process.env.CHAT_MODEL || 'gpt-4o-mini';

async function medicalReview(preauth){
  // Fetch matching clinical criteria for requested procedure codes
  const db = await getDb();
  const criteriaColl = db.collection('clinical_criteria');
  const codes = preauth.requestedProcedureCodes || [];
  const criteriaDocs = await criteriaColl.find({ procedureCode: { $in: codes } }).toArray();

  if (openaiKey){
    const client = new OpenAI({ apiKey: openaiKey });
    const prompt = `You are a medical-review assistant.\n\nPreauth request:\n${JSON.stringify(preauth, null, 2)}\n\nClinical criteria documents:\n${JSON.stringify(criteriaDocs, null, 2)}\n\nProvide a JSON object with fields: necessary (true/false), reasons (array of strings), confidence (0-1). Keep it concise.`;
    const resp = await client.chat.completions.create({ model: chatModel, messages: [{ role: 'user', content: prompt }], max_tokens: 500 });
    const text = resp.choices?.[0]?.message?.content || '';
    try{
      const json = JSON.parse(text);
      return json;
    }catch(e){
      return { necessary: false, reasons: ['LLM output parse error; returning conservative denial.'], confidence: 0.3 };
    }
  } else {
    // Deterministic rule-based fallback: if any criteria tag is severe and notes reference imaging/acute -> necessary
    let necessary = false;
    const reasons = [];
    for (const c of criteriaDocs){
      if ((c.severityTags || []).includes('severe')){
        if (/MRI|imaging|acute/i.test(preauth.clinicalNotes)){
          necessary = true;
          reasons.push(`Matches severe criteria for ${c.procedureCode} with imaging.`);
        } else {
          reasons.push(`Severe criteria for ${c.procedureCode} but no imaging mentioned.`);
        }
      } else if ((c.severityTags || []).includes('moderate')){
        if (/conservative|PT|therapy|weeks/i.test(preauth.clinicalNotes)){
          necessary = true;
          reasons.push(`Moderate criteria met for ${c.procedureCode} (conservative therapy tried).`);
        }
      } else if ((c.severityTags || []).includes('experimental')){
        reasons.push(`Procedure ${c.procedureCode} flagged experimental; likely not necessary.`);
      } else {
        reasons.push(`Procedure ${c.procedureCode} criteria reviewed.`);
      }
    }
    return { necessary, reasons, confidence: necessary ? 0.8 : 0.4 };
  }
}

module.exports = { medicalReview };
