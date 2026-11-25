const { mongoose } = require('../db');
const { Schema } = mongoose;

const TransitionSchema = new Schema({
  from: { type: String },
  to: { type: String, required: true },
  at: { type: Date, default: () => new Date() },
  by: { type: String },
  note: { type: String }
}, { _id: false });

const TradeSchema = new Schema({
  tradeId: { type: String, required: true, unique: true },
  assetClass: { type: String, required: true },
  counterparty: { type: String, required: true },
  currentState: { type: String, required: true, index: true },
  stateHistory: { type: [TransitionSchema], default: [] },
  metadata: { createdAt: { type: Date, default: () => new Date() }, updatedAt: { type: Date, default: () => new Date() } },
  version: { type: Number, default: 1 }
});

TradeSchema.pre('save', function (next) {
  this.metadata.updatedAt = new Date();
  next();
});

const Trade = mongoose.models.Trade || mongoose.model('Trade', TradeSchema, 'trades');
module.exports = Trade;
