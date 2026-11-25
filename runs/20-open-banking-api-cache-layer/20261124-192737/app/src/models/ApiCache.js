const { mongoose } = require('../mongo');
const { Schema } = require('mongoose');

const ApiCacheSchema = new Schema({
  key: { type: String, required: true, index: { unique: true } },
  response: { type: Schema.Types.Mixed },
  statusCode: { type: Number },
  headers: { type: Schema.Types.Mixed },
  cachedAt: { type: Date, default: Date.now },
  expiresAt: { type: Date, required: true },
  staleUntil: { type: Date, required: true }
}, { collection: 'api_cache' });

// TTL index on expiresAt so documents are removed when expiresAt <= now
ApiCacheSchema.index({ expiresAt: 1 }, { expireAfterSeconds: 0 });

module.exports = mongoose.models.ApiCache || mongoose.model('ApiCache', ApiCacheSchema);
