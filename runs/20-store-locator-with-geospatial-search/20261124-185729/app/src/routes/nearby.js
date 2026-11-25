const express = require('express');
const router = express.Router();
const Store = require('../models/store');

// GET /nearby?lat=..&lon=..&radiusMeters=..
router.get('/', async (req, res) => {
  try {
    const lat = parseFloat(req.query.lat);
    const lon = parseFloat(req.query.lon);
    const radius = parseFloat(req.query.radiusMeters) || 5000; // default 5km

    if (Number.isNaN(lat) || Number.isNaN(lon)) {
      return res.status(400).json({ error: 'lat and lon query parameters are required and must be numbers' });
    }

    const pipeline = [
      {
        $geoNear: {
          near: { type: 'Point', coordinates: [lon, lat] },
          distanceField: 'distanceMeters',
          spherical: true,
          maxDistance: radius
        }
      },
      {
        $project: {
          name: 1,
          location: 1,
          opening_hours: 1,
          stock: 1,
          distanceMeters: 1
        }
      }
    ];

    const results = await Store.aggregate(pipeline).exec();
    res.json({ count: results.length, results });
  } catch (err) {
    console.error('Error in /nearby:', err);
    res.status(500).json({ error: 'internal_error' });
  }
});

module.exports = router;
