const { mongoose } = require('../db');
const { Schema } = mongoose;

const WardSummarySchema = new Schema({
  wardId: { type: String, required: true, unique: true },
  counts: {
    occupied: { type: Number, default: 0 },
    available: { type: Number, default: 0 },
    cleaning: { type: Number, default: 0 }
  },
  capacity: { type: Number, default: 0 }
}, { timestamps: true });

module.exports = mongoose.model('WardSummary', WardSummarySchema);
