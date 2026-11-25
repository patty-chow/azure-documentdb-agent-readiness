const mongoose = require('mongoose');
const { Schema } = mongoose;

const SourceSchema = new Schema({}, { strict: false });

const CustomerSchema = new Schema({
  customerId: { type: String, required: true, index: true },
  sources: {
    crm: { type: SourceSchema, default: {} },
    ecommerce: { type: SourceSchema, default: {} },
    support: { type: SourceSchema, default: {} }
  },
  createdAt: { type: Date, default: () => new Date() },
  updatedAt: { type: Date, default: () => new Date() }
});

// Ensure a unique index on customerId (seed script will call createIndexes as well)
CustomerSchema.index({ customerId: 1 }, { unique: true });

function createModel(db) {
  // db is a mongoose.Connection returned by connection.useDb
  return db.model('Customer', CustomerSchema);
}

module.exports = { createModel };
