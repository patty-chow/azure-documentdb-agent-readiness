const mongoose = require('mongoose');

const InteractionSchema = new mongoose.Schema({
  drugA: { type: String, required: true, index: true },
  drugB: { type: String, required: true, index: true },
  normalizedPair: { type: String, required: true, unique: true, index: true },
  severityScore: { type: Number, default: null },
  clinicalRecommendation: { type: String, default: '' },
  evidence: { type: [String], default: [] },
  updatedAt: { type: Date, default: Date.now }
}, { collection: 'interactions' });

InteractionSchema.pre('save', function(next) {
  this.updatedAt = new Date();
  next();
});

module.exports = mongoose.models.Interaction || mongoose.model('Interaction', InteractionSchema);
