const mongoose = require('mongoose');

const ValuationSchema = new mongoose.Schema({
  amount: { type: Number, required: true },
  currency: { type: String, required: true }
}, { _id: false });

const CollateralSchema = new mongoose.Schema({
  assetId: { type: String, required: true, index: true },
  version: { type: Number, required: true, index: true },
  createdAt: { type: Date, required: true, default: () => new Date(), index: true },
  valuation: { type: ValuationSchema, required: true },
  metadata: { type: mongoose.Schema.Types.Mixed },
  llmTags: {
    assetType: { type: String },
    eligibilityTier: { type: String }
  },
  // Optional embedding field (array of numbers). Embeddings are optional in this sample.
  embedding: { type: [Number], default: undefined }
}, {
  collection: 'collateral_assets'
});

// Compound index to support quick lookup of latest version per asset
CollateralSchema.index({ assetId: 1, version: -1 });

module.exports = mongoose.model('CollateralAsset', CollateralSchema);
