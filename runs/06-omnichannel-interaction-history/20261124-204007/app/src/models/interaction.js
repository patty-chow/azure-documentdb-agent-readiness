const mongoose = require('mongoose');

const InteractionSchema = new mongoose.Schema({
  interactionId: { type: String, required: true, unique: true },
  customerId: { type: String, required: true, index: true },
  channel: { type: String, required: true, enum: ['web','mobile','email','call_center'] },
  timestamp: { type: Date, required: true, index: true },
  direction: { type: String, enum: ['inbound','outbound'], default: 'inbound' },
  subject: String,
  body: mongoose.Schema.Types.Mixed,
  metadata: mongoose.Schema.Types.Mixed
}, { collection: 'interactions' });

// Compound indexes required by the sample
InteractionSchema.index({ customerId: 1, timestamp: -1 });
InteractionSchema.index({ channel: 1, timestamp: -1 });

module.exports = mongoose.model('Interaction', InteractionSchema);
