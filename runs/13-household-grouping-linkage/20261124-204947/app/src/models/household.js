const { Schema, model, Types } = require('mongoose');

const HouseholdSchema = new Schema({
  members: [{ type: Types.ObjectId, ref: 'Customer' }],
  createdAt: { type: Date, default: () => new Date() },
  meta: Schema.Types.Mixed
});

HouseholdSchema.index({ members: 1 });

module.exports = model('Household', HouseholdSchema);
