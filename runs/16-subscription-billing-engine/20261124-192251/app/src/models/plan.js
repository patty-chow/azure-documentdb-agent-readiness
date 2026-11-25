const { mongoose } = require('../db');
const Schema = mongoose.Schema;

const PlanSchema = new Schema({
  planId: { type: String, required: true, unique: true },
  name: { type: String, required: true },
  priceCents: { type: Number, required: true },
  interval: { type: String, enum: ['monthly','yearly'], default: 'monthly' }
}, { timestamps: true });

module.exports = mongoose.model('Plan', PlanSchema);
