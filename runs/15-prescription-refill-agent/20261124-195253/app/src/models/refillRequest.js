const { Schema } = require('mongoose');

const RefillRequestSchema = new Schema({
  patientId: { type: String, required: true, index: true },
  prescriptionId: { type: String, required: true, index: true },
  requestedAt: { type: Date, default: () => new Date(), index: true },
  status: { type: String, default: 'requested' },
  note: { type: String }
}, { timestamps: true });

module.exports = RefillRequestSchema;
