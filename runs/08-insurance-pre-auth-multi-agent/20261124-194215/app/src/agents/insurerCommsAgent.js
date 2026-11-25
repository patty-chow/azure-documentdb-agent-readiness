require('dotenv').config();
const OpenAI = require('openai');
const openaiKey = process.env.OPENAI_API_KEY;
const chatModel = process.env.CHAT_MODEL || 'gpt-4o-mini';

async function draftSubmission(preauth, assessment){
  const header = `To: Insurance Medical Review\nFrom: ${preauth.clinician}\nRe: Pre-authorization ${preauth._id}\n\n`;
  if (openaiKey){
    const client = new OpenAI({ apiKey: openaiKey });
    const prompt = `Draft a professional submission letter for a medical pre-authorization based on the following:\n\nPreauth request:\n${JSON.stringify(preauth, null, 2)}\n\nAssessment:\n${JSON.stringify(assessment, null, 2)}\n\nInclude a short rationale and requested action. Return only the letter text.`;
    const resp = await client.chat.completions.create({ model: chatModel, messages: [{ role: 'user', content: prompt }], max_tokens: 700 });
    const text = resp.choices?.[0]?.message?.content || '';
    return header + text;
  } else {
    // Simple templated letter
    const lines = [];
    lines.push(header);
    lines.push(`Patient: ${preauth.patientId}`);
    lines.push(`Requested codes: ${preauth.requestedProcedureCodes.join(', ')}`);
    lines.push('\nClinical notes:\n' + preauth.clinicalNotes + '\n');
    lines.push('Assessment:');
    lines.push(assessment.necessary ? 'Medical necessity supported.' : 'Medical necessity NOT supported based on available criteria.');
    lines.push('\nReasons:');
    for (const r of (assessment.reasons || [])) lines.push('- ' + r);
    lines.push('\nRequested action: Please process this pre-authorization per standard review workflows.');
    return lines.join('\n');
  }
}

module.exports = { draftSubmission };
