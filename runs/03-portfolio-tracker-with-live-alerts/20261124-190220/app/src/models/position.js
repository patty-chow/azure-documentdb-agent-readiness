const { Schema } = require('mongoose');

const PositionSchema = new Schema({
  userId: { type: String, required: true, index: true },
  symbol: { type: String, required: true, index: true },
  shares: { type: Number, required: true },
  avgCost: { type: Number, required: true },
  currentPrice: { type: Number, required: true },
  sector: { type: String, index: true },
  updatedAt: { type: Date, default: Date.now },
  schemaVersion: { type: Number, default: 1 }
}, { timestamps: true });

// Compound index to support per-user symbol lookups
PositionSchema.index({ userId: 1, symbol: 1 });

module.exports = PositionSchema;
