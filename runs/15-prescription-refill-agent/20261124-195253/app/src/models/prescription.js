const { Schema } = require('mongoose');

const PrescriptionSchema = new Schema({
  patientId: { type: String, required: true, index: true },
  prescriptionId: { type: String, required: true, unique: true },
  drugName: { type: String, required: true },
  daysSupply: { type: Number, required: true },
  refillCount: { type: Number, required: true },
  lastFilledAt: { type: Date, required: true },
  active: { type: Boolean, default: true, index: true }
}, { timestamps: true });

module.exports = PrescriptionSchema;
