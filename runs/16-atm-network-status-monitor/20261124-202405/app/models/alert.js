const { Schema, model } = require('mongoose');

const AlertSchema = new Schema({
  timestamp: { type: Date, default: () => new Date() },
  availability: { type: Number, required: true },
  threshold: { type: Number, required: true },
  reason: { type: String }
});

module.exports = model('Alert', AlertSchema);
