const { mongoose } = require('../db');
const { Schema } = mongoose;

const BedSchema = new Schema({
  bedId: { type: String, required: true, index: true },
  wardId: { type: String, required: true, index: true },
  status: { type: String, required: true, enum: ['occupied', 'available', 'cleaning'], index: true },
  lastStatusChangeAt: { type: Date, default: Date.now },
  // When entering 'cleaning' state, set cleaningExpiresAt to Date.now() + TTL seconds
  cleaningExpiresAt: { type: Date, default: null }
}, { timestamps: true });

// Indexes: TTL on cleaningExpiresAt (expireAfterSeconds to be set by code to 0)
// Additional compound index to support queries by ward+status
BedSchema.index({ wardId: 1, status: 1 });

module.exports = mongoose.model('Bed', BedSchema);
