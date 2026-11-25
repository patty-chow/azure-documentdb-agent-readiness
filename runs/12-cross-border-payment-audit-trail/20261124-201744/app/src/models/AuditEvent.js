const { mongoose } = require('../db');
const { Schema } = mongoose;

const AuditEventSchema = new Schema({
  _id: { type: String }, // allow client to provide deterministic id for idempotent seeds (e.g., `${paymentReference}_${stage}`)
  paymentReference: { type: String, required: true, index: true },
  stage: { type: String, required: true, enum: ['initiated', 'routed', 'fx_converted', 'settled'] },
  stageTimestamp: { type: Date, required: true },
  details: { type: Schema.Types.Mixed },
  createdAt: { type: Date, default: () => new Date(), immutable: true }
}, { collection: 'audit_events' });

// Compound index for equality + sort (paymentReference eq, sort by stageTimestamp)
AuditEventSchema.index({ paymentReference: 1, stageTimestamp: 1 });

// Prevent updates at application layer
function preventUpdate(next) {
  const err = new Error('AuditEvent is immutable: updates/replacements are not allowed');
  err.name = 'ImmutableDocumentError';
  next(err);
}

// Disallow updates through the common update/replace query methods
AuditEventSchema.pre('updateOne', preventUpdate);
AuditEventSchema.pre('updateMany', preventUpdate);
AuditEventSchema.pre('findOneAndUpdate', preventUpdate);
AuditEventSchema.pre('findOneAndReplace', preventUpdate);
AuditEventSchema.pre('replaceOne', preventUpdate);
AuditEventSchema.pre('bulkWrite', function(next) {
  // inspect ops for any update/replace types
  const hasUpdate = (this && this._operations && this._operations.some && this._operations.some(op => {
    return op.updateOne || op.updateMany || op.replaceOne || op.findOneAndUpdate || op.findOneAndReplace;
  }));
  if (hasUpdate) return preventUpdate(next);
  next();
});

// Prevent saving an existing document via save()
AuditEventSchema.pre('save', function(next) {
  if (!this.isNew) {
    const err = new Error('AuditEvent is immutable: saving existing documents is not allowed');
    err.name = 'ImmutableDocumentError';
    return next(err);
  }
  next();
});

// Helper: get timeline aggregation
AuditEventSchema.statics.getTimeline = async function(paymentReference) {
  return this.aggregate([
    { $match: { paymentReference } },
    { $sort: { stageTimestamp: 1 } }
  ]).exec();
};

const AuditEvent = mongoose.model('AuditEvent', AuditEventSchema);
module.exports = AuditEvent;
