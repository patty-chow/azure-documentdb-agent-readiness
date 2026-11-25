const { Schema } = require('mongoose');

const AgentMemorySchema = new Schema({
  patientId: { type: String, required: true, unique: true },
  lastMedication: { type: String },
  updatedAt: { type: Date, default: () => new Date() }
});

module.exports = AgentMemorySchema;
