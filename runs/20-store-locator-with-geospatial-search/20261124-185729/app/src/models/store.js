const mongoose = require('mongoose');

const StoreSchema = new mongoose.Schema({
  name: { type: String, required: true },
  location: {
    type: { type: String, enum: ['Point'], required: true },
    coordinates: { type: [Number], required: true } // [lon, lat]
  },
  opening_hours: {
    // simple example: [{ day: 'Mon', open: '09:00', close: '17:00' }]
    type: [{ day: String, open: String, close: String }],
    default: []
  },
  stock: {
    // map of sku -> quantity
    type: Map,
    of: Number,
    default: {}
  }
}, { collection: 'stores' });

// Ensure 2dsphere index on location
StoreSchema.index({ location: '2dsphere' });

module.exports = mongoose.models.Store || mongoose.model('Store', StoreSchema);
