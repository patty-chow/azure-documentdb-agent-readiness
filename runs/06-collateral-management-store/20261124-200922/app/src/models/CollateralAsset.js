const mongoose = require('mongoose');

const ValuationSchema = new mongoose.Schema({
  amount: { type: Number, required: true },
  currency: { type: String, default: 'USD' }
}, { _id: false });

const LLMTagSchema = new mongoose.Schema({
  assetType: { type: String },
  eligibilityTier: { type: String }
}, { _id: false });

const CollateralAssetSchema = new mongoose.Schema({
  assetId: { type: String, required: true, index: true },
  version: { type: Number, required: true },
  createdAt: { type: Date, default: () => new Date(), index: true },
  valuation: { type: ValuationSchema, required: true },
  liability: { type: Number, default: 0 },
  metadata: { type: mongoose.Schema.Types.Mixed },
  llmTags: { type: LLMTagSchema },
  embedding: { type: [Number] }
}, { collection: 'collateral_assets' });

// Compound index to support latest-version queries
CollateralAssetSchema.index({ assetId: 1, version: -1 }, { name: 'asset_version_idx' });
CollateralAssetSchema.index({ createdAt: 1 }, { name: 'createdAt_idx' });
CollateralAssetSchema.index({ assetId: 1, createdAt: -1 }, { name: 'asset_createdAt_idx' });

// unique per assetId+version to allow idempotent upserts
CollateralAssetSchema.index({ assetId: 1, version: 1 }, { unique: true, name: 'asset_version_unique' });

module.exports = mongoose.model('CollateralAsset', CollateralAssetSchema);
