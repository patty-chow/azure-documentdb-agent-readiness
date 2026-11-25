const express = require('express');
const { connect, mongoose } = require('./db');
const CustomerSchema = require('./models/customer');
const HouseholdSchema = require('./models/household');

const Customer = mongoose.model('Customer', CustomerSchema);
const Household = mongoose.model('Household', HouseholdSchema);

async function createApp() {
  await connect();
  const app = express();
  app.use(express.json());

  app.get('/households/:id/clv', async (req, res) => {
    try {
      const id = req.params.id;
      const household = await Household.findById(id).populate('members').exec();
      if (!household) return res.status(404).json({ error: 'Household not found' });
      const clvTotal = household.members.reduce((s, m) => s + (m.clv || 0), 0);
      res.json({ householdId: id, clvTotal });
    } catch (err) {
      console.error(err);
      res.status(500).json({ error: 'internal' });
    }
  });

  app.get('/households/:id/products', async (req, res) => {
    try {
      const id = req.params.id;
      const household = await Household.findById(id).populate('members').exec();
      if (!household) return res.status(404).json({ error: 'Household not found' });
      const tally = {};
      household.members.forEach(m => {
        (m.products || []).forEach(p => {
          const pid = p.productId || 'unknown';
          tally[pid] = (tally[pid] || 0) + (p.quantity || 1);
        });
      });
      const products = Object.entries(tally).map(([productId, count]) => ({ productId, count }));
      res.json({ householdId: id, products });
    } catch (err) {
      console.error(err);
      res.status(500).json({ error: 'internal' });
    }
  });

  // Simple endpoint to list households with member counts
  app.get('/households', async (req, res) => {
    const list = await Household.aggregate([
      { $project: { memberCount: { $size: '$members' }, createdAt: 1 } },
      { $sort: { memberCount: -1 } },
      { $limit: 100 }
    ]);
    res.json(list);
  });

  return app;
}

if (require.main === module) {
  createApp().then(app => {
    const port = process.env.PORT || 3000;
    app.listen(port, () => console.log(`Server listening on ${port}`));
  }).catch(err => {
    console.error('Failed to start app', err);
    process.exit(1);
  });
}

module.exports = { createApp };
