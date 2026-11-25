const { getDb } = require('./db');
const { generateRecoveryMessage } = require('./agents/copyGenerator');
const { sendAccordingToPreference, logDelivery } = require('./agents/channelAgent');

async function findAbandonedCarts(db) {
  const carts = db.collection('carts');
  const twoHoursAgo = new Date(Date.now() - 1000 * 60 * 60 * 2);

  // Find carts with updatedAt < twoHoursAgo and processedAt is null or not set
  const query = {
    updatedAt: { $lt: twoHoursAgo },
    $or: [{ processedAt: { $exists: false } }, { processedAt: null }]
  };

  // sort newest-first
  const docs = await carts.find(query).sort({ updatedAt: -1 }).toArray();
  return docs;
}

async function orchestrate() {
  const db = await getDb();
  const customers = db.collection('customers');

  const carts = await findAbandonedCarts(db);
  console.log(`Found ${carts.length} abandoned carts to process.`);

  for (const cart of carts) {
    try {
      const customer = await customers.findOne({ customerId: cart.customerId });
      if (!customer) {
        console.warn(`No customer record for cart ${cart.cartId}, skipping.`);
        continue;
      }

      const message = await generateRecoveryMessage({ customer, cart });
      const delivery = await sendAccordingToPreference(customer, message);

      const entry = { ts: new Date(), status: delivery.success ? 'sent' : 'failed', meta: delivery };
      await logDelivery(cart.cartId, entry);
      console.log(`Processed cart ${cart.cartId} for customer ${customer.customerId}: ${entry.status}`);
    } catch (err) {
      console.error(`Failed to process cart ${cart.cartId}:`, err);
      // record failure in deliveryLog
      await logDelivery(cart.cartId, { ts: new Date(), status: 'error', error: String(err) });
    }
  }
}

orchestrate().then(()=>process.exit(0)).catch(err=>{ console.error(err); process.exit(1); });
