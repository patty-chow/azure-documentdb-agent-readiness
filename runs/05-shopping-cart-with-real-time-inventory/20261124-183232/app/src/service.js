const { connect, mongoose } = require('./db');
const { Inventory, Cart } = require('./models');

async function addToCart(userId, productId, quantity, opts = {}) {
  await connect();
  const maxRetries = opts.maxRetries ?? 3;
  const backoffBase = opts.backoffBase ?? 100; // ms

  for (let attempt = 1; attempt <= maxRetries; attempt++) {
    const session = await mongoose.startSession();
    try {
      session.startTransaction();

      // Load inventory inside session and check stock
      const product = await Inventory.findById(productId).session(session);
      if (!product) {
        throw new Error('ProductNotFound');
      }

      if (product.stock < quantity) {
        // Clear, domain-specific error when stock exhausted
        throw new Error('OutOfStock');
      }

      // Decrement stock with conditional update to avoid oversell
      const res = await Inventory.updateOne({ _id: productId, stock: { $gte: quantity } }, { $inc: { stock: -quantity } }).session(session);
      if (res.modifiedCount === 0) {
        // Another concurrent updater beat us to it or not enough stock
        throw new Error('OutOfStock');
      }

      // Read or create cart, then modify in-session
      let cart = await Cart.findOne({ userId }).session(session);
      if (!cart) {
        cart = new Cart({ userId, items: [] });
      }

      const existing = cart.items.find(it => it.productId?.toString() === productId.toString());
      if (existing) {
        existing.quantity += quantity;
      } else {
        cart.items.push({ productId, sku: product.sku, name: product.name, price: product.price, quantity });
      }

      await cart.save({ session });

      await session.commitTransaction();
      session.endSession();
      return { success: true, cart };
    } catch (err) {
      await session.abortTransaction().catch(()=>{});
      session.endSession();

      // If out of stock, surface immediately without retries
      if (err && err.message === 'OutOfStock') {
        return { success: false, error: 'OutOfStock' };
      }

      // Optimistic concurrency or transient errors: retry
      if (attempt < maxRetries) {
        const wait = backoffBase * Math.pow(2, attempt - 1);
        await new Promise(res => setTimeout(res, wait));
        continue;
      }

      return { success: false, error: err.message || String(err) };
    }
  }
}

module.exports = { addToCart };
