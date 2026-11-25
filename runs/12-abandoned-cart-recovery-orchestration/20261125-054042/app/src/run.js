require('dotenv').config();
const { getDb } = require('./db');
const CopyAgent = require('./agents/copyAgent');
const ChannelAgent = require('./agents/channelAgent');

async function runOnce() {
  const db = await getDb();
  const cartsColl = db.collection('carts');
  const customersColl = db.collection('customers');
  const logsColl = db.collection('recovery_logs');

  // ensure indexes: lastUpdated index to support the abandoned query
  await cartsColl.createIndex({ lastUpdated: 1 });
  await logsColl.createIndex({ cartId: 1 });

  // find carts abandoned for >2 hours and not yet processed by this sample
  const cutoff = new Date(Date.now() - 1000 * 60 * 60 * 2);
  const query = { status: 'abandoned', lastUpdated: { $lte: cutoff }, 'sample': 'abandoned-cart-sample-12' };
  const carts = await cartsColl.find(query).toArray();

  console.log(`Found ${carts.length} abandoned carts older than 2 hours.`);

  const copyAgent = new CopyAgent();
  const channelAgent = new ChannelAgent();

  for (const cart of carts) {
    try {
      const customer = await customersColl.findOne({ _id: cart.customerId });
      if (!customer) {
        console.warn(`No customer found for cart ${cart._id}`);
        continue;
      }

      const message = await copyAgent.generateMessage(cart, customer);
      const sendResult = await channelAgent.send(customer, message);

      const log = {
        cartId: cart._id,
        customerId: cart.customerId,
        channel: customer.preferredChannel || 'email',
        message,
        result: sendResult,
        timestamp: new Date(),
      };
      await logsColl.insertOne(log);
      console.log(`Logged outcome for cart ${cart._id}`);
    } catch (err) {
      console.error('Error processing cart', cart._id, err);
    }
  }
}

if (require.main === module) {
  runOnce().then(() => process.exit(0)).catch(err => { console.error(err); process.exit(1); });
}

module.exports = { runOnce };
