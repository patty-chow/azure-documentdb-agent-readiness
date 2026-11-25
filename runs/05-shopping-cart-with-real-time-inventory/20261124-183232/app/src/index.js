const express = require('express');
const morgan = require('morgan');
const { connect } = require('./db');
const { addToCart } = require('./service');

const app = express();
app.use(express.json());
app.use(morgan('dev'));

app.post('/cart/:userId/add', async (req, res) => {
  const userId = req.params.userId;
  const { productId, quantity } = req.body;
  if (!productId || !quantity || quantity <= 0) {
    return res.status(400).json({ error: 'productId and quantity>0 required' });
  }

  try {
    const result = await addToCart(userId, productId, quantity);
    if (!result.success) {
      if (result.error === 'OutOfStock') return res.status(409).json({ error: 'OutOfStock' });
      return res.status(500).json({ error: result.error });
    }
    return res.json({ cart: result.cart });
  } catch (err) {
    console.error(err);
    return res.status(500).json({ error: 'internal' });
  }
});

const port = process.env.PORT || 3000;
(async () => {
  await connect();
  app.listen(port, () => {
    console.log('Server listening on', port);
  });
})();
