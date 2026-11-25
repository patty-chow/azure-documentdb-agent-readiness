// Agent that optionally uses LangChain/OpenAI when OPENAI_API_KEY is present

function buildPrompt(drugA, drugB, evidence) {
  const system = `You are a clinical pharmacist assistant. For the given drug pair, return a JSON object with keys: severity (number 0-10), recommendation (short string <=200 chars). Provide a numeric severity (0 = no interaction, 10 = severe/life-threatening). Use evidence when available.`;
  const human = `Drugs: ${drugA} / ${drugB}\nEvidence:\n${evidence.join('\n- ')}\n\nRespond ONLY with valid JSON like: {"severity": 4, "recommendation": "..."}`;
  return { system, human };
}

async function assessWithLLM(drugA, drugB, evidence) {
  // If OPENAI_API_KEY not set, fall back to heuristic
  if (!process.env.OPENAI_API_KEY) {
    const joined = evidence.join(' ').toLowerCase();
    let score = 0;
    if (joined.includes('contraind')) score = 9;
    else if (joined.includes('avoid')) score = 8;
    else if (joined.includes('monitor')) score = 5;
    else if (joined.length > 0) score = 3;
    return { severity: score, recommendation: evidence.slice(0,1).join(' ') || 'No known severe interaction.' };
  }

  // Lazy-load langchain to avoid test-time dependency issues
  let LangOpenAI, ChatPromptTemplate, HumanMessagePromptTemplate, SystemMessagePromptTemplate, LLMChain;
  try {
    ({ OpenAI: LangOpenAI } = require('langchain/llms/openai'));
    ({ ChatPromptTemplate, HumanMessagePromptTemplate, SystemMessagePromptTemplate } = require('langchain'));
    ({ LLMChain } = require('langchain'));
  } catch (err) {
    console.error('LangChain is not available, falling back to heuristic:', err.message);
    return { severity: 0, recommendation: 'LLM not available; no assessment.' };
  }

  const { system, human } = buildPrompt(drugA, drugB, evidence);
  const model = new LangOpenAI({ openAIApiKey: process.env.OPENAI_API_KEY, temperature: 0 });
  const prompt = ChatPromptTemplate.fromPromptMessages([
    SystemMessagePromptTemplate.fromTemplate(system),
    HumanMessagePromptTemplate.fromTemplate(human)
  ]);
  const chain = new LLMChain({ llm: model, prompt });
  try {
    const resp = await chain.call({});
    const text = resp?.text || resp?.response || '';
    const m = text.match(/\{[\s\S]*\}/);
    if (!m) throw new Error('No JSON in LLM response');
    const parsed = JSON.parse(m[0]);
    return { severity: Number(parsed.severity) || 0, recommendation: String(parsed.recommendation || '') };
  } catch (err) {
    console.error('LLM error, falling back to heuristic:', err.message);
    return { severity: 0, recommendation: 'Could not assess automatically; please consult reference.' };
  }
}

module.exports = { assessWithLLM };
