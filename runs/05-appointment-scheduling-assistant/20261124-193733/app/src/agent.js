require('dotenv').config();
const { ChatOpenAI } = require('langchain/chat_models/openai');
const { BufferMemory } = require('langchain/memory');

const store = require('./store');

const llm = new ChatOpenAI({ openAIApiKey: process.env.OPENAI_API_KEY, modelName: process.env.OPENAI_MODEL || 'gpt-4o', temperature: 0 });

// Simple in-process conversation memory per user using LangChain's BufferMemory abstraction
const memories = new Map();
function getMemoryForUser(userId) {
  if (!memories.has(userId)) {
    const m = new BufferMemory({ memoryKey: 'chat_history' });
    memories.set(userId, m);
  }
  return memories.get(userId);
}

const tools = {
  findAvailableSlots: {
    name: 'findAvailableSlots',
    description: 'Find available slots for a provider in a time window. Args: { providerId, fromISO, toISO, limit }',
    func: async (args) => {
      const from = args.fromISO ? new Date(args.fromISO) : undefined;
      const to = args.toISO ? new Date(args.toISO) : undefined;
      const slots = await store.findAvailableSlots(args.providerId, from, to, args.limit || 10);
      return JSON.stringify(slots, null, 2);
    }
  },
  createAppointment: {
    name: 'createAppointment',
    description: "Create an appointment for patientId on slotId. Args: { patientId, slotId, notes }",
    func: async (args) => {
      const res = await store.createAppointmentAtomic(args.patientId, args.slotId, args.notes || '');
      return JSON.stringify(res, null, 2);
    }
  },
  rescheduleAppointment: {
    name: 'rescheduleAppointment',
    description: 'Reschedule an appointment to a targetSlotId. Args: { appointmentId, targetSlotId }',
    func: async (args) => {
      const res = await store.rescheduleAppointmentAtomic(args.appointmentId, args.targetSlotId);
      return JSON.stringify(res, null, 2);
    }
  },
  cancelAppointment: {
    name: 'cancelAppointment',
    description: 'Cancel an appointment and free its slot. Args: { appointmentId }',
    func: async (args) => {
      const res = await store.cancelAppointment(args.appointmentId);
      return JSON.stringify(res, null, 2);
    }
  }
};

async function handleMessage(userId, message) {
  const memory = getMemoryForUser(userId);
  // add user message to memory
  await memory.saveContext({ input: message }, { output: '' });

  // Build a prompt describing tools and asking for a JSON decision
  const toolDescriptions = Object.values(tools).map(t => `- ${t.name}: ${t.description}`).join('\n');

  const systemPrompt = `You are an appointment scheduling assistant. You have the following tools available:\n${toolDescriptions}\n\nWhen the user asks to perform an action you should respond with a JSON object describing the tool to call and the arguments. The JSON must be the only thing in your response and match: { "tool": "toolName", "args": { ... } }. If the user is asking for information only or a conversational reply, return { "tool": "none", "response": "chat response here" }.`;

  const res = await llm.call([{
    role: 'system',
    content: systemPrompt
  }, {
    role: 'user',
    content: message
  }]);

  const text = res.text?.trim() || res[0]?.text || '';

  let parsed;
  try {
    parsed = JSON.parse(text);
  } catch (e) {
    // If parsing fails, fall back to a chat response
    await memory.saveContext({ input: message }, { output: text });
    return { type: 'chat', message: 'Sorry, I could not parse the LLM response. Raw: ' + text };
  }

  if (parsed.tool === 'none') {
    await memory.saveContext({ input: message }, { output: parsed.response || 'OK' });
    return { type: 'chat', message: parsed.response };
  }

  const tool = tools[parsed.tool];
  if (!tool) {
    return { type: 'error', message: `Unknown tool: ${parsed.tool}` };
  }

  const toolResult = await tool.func(parsed.args || {});
  // Save tool result to memory
  await memory.saveContext({ input: message }, { output: toolResult });
  return { type: 'tool_result', tool: parsed.tool, result: toolResult };
}

module.exports = { handleMessage };
