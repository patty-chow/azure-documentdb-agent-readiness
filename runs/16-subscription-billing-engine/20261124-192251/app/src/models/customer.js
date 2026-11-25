const { mongoose } = require('../db');
const Schema = mongoose.Schema;

const CustomerSchema = new Schema({
  name: { type: String, required: true },
  email: { type: String, required: true, unique: true },
  metadata: { type: Schema.Types.Mixed }
}, { timestamps: true });

module.exports = mongoose.model('Customer', CustomerSchema);
