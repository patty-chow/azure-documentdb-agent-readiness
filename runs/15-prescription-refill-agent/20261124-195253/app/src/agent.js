const { connect, mongoose } = require('./db');
const PrescriptionSchema = require('./models/Prescription');
const RefillRequestSchema = require('./models/RefillRequest');
const AgentMemorySchema = require('./models/AgentMemory');

const Prescription = mongoose.model('Prescription', PrescriptionSchema);
const RefillRequest = mongoose.model('RefillRequest', RefillRequestSchema);
const AgentMemory = mongoose.model('AgentMemory', AgentMemorySchema);

// Minimal rule-based agent for demo. Pluggable for an LLM-based agent later.
class Agent {
  constructor() {}

  // helper to normalize medication names
  normalizeDrugName(name) {
    if (!name) return null;
    return name.trim().toLowerCase();
  }

  async process(patientId, message) {
    await connect();

    const lc = message.toLowerCase();
    const wantsRefill = lc.includes('refill');
    if (!wantsRefill) return { text: "I can help with refills — say 'refill <drug>' or 'refill my blood pressure medication'." };

    // extract a drug name if present with a simple regex (words with letters)
    const drugMatch = message.match(/refill(?: my| the)? ([a-zA-Z0-9\- ]+)/i);
    let drugName = drugMatch ? drugMatch[1].trim() : null;

    // if drugName is a vague term like 'blood pressure medication', consult memory
    const vagueMap = {
      'blood pressure medication': 'lisinopril',
      'bp medication': 'lisinopril'
    };

    if (drugName) {
      const lower = drugName.toLowerCase();
      if (vagueMap[lower]) drugName = vagueMap[lower];
    }

    // if no explicit drug found, check agent memory for this patient
    if (!drugName) {
      const mem = await AgentMemory.findOne({ patientId });
      if (mem && mem.lastMedication) {
        drugName = mem.lastMedication;
      }
    }

    if (!drugName) {
      return { text: 'Which medication would you like to refill?' };
    }

    const normDrug = this.normalizeDrugName(drugName);

    // Find active prescription for this patient and drug (case-insensitive)
    const prescription = await Prescription.findOne({
      patientId,
      active: true,
      drugName: { $regex: `^${normDrug}$`, $options: 'i' }
    });

    if (!prescription) {
      return { text: `No active prescription found for '${drugName}'.` };
    }

    // Update memory with this medication
    await AgentMemory.findOneAndUpdate(
      { patientId },
      { lastMedication: prescription.drugName, updatedAt: new Date() },
      { upsert: true }
    );

    // Eligibility logic: allow refill if refillCount > 0 and days remaining <= 3
    const now = new Date();
    const daysSinceLast = Math.floor((now - prescription.lastFilledAt) / (1000 * 60 * 60 * 24));
    const daysRemaining = prescription.daysSupply - daysSinceLast;
    const eligible = prescription.refillCount > 0 && daysRemaining <= 3;

    if (!eligible) {
      return { text: `Prescription for ${prescription.drugName} is not eligible yet. Days remaining: ${daysRemaining}. Refill count left: ${prescription.refillCount}` };
    }

    // Create refill request
    const rr = new RefillRequest({
      patientId,
      prescriptionId: prescription.prescriptionId,
      status: 'requested',
      requestedAt: new Date(),
      note: `Requested via agent for ${prescription.drugName}`
    });
    await rr.save();

    // decrement refillCount
    prescription.refillCount = prescription.refillCount - 1;
    await prescription.save();

    return { text: `Refill requested for ${prescription.drugName}. Refill request id: ${rr._id}` };
  }
}

module.exports = Agent;
