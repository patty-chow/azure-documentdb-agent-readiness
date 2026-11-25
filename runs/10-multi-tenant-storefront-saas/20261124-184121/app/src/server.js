const express = require('express');
const { connect } = require('./mongoose');
const { Product } = require('./models/index');
const ProductRepo = require('./repos/productRepo');

const app = express();
app.use(express.json());

app.get('/health', (req, res) => res.json({ status: 'ok' }));

// Example endpoint: list products for a tenant
app.get('/tenants/:tenantId/products', async (req, res) => {
  try {
    await connect();
    const repo = new ProductRepo(require('./models'), req.params.tenantId);
    const items = await repo.listAll();
    res.json(items);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => console.log(`Server listening on ${PORT}`));
