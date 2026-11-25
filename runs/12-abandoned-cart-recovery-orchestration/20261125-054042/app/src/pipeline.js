import { getClientAsync } from './db.js';
import { generateMessage } from './agents/copyAgent.js';
import { sendNotification } from './agents/channelAgent.js';

const TWO_HOURS_MS = 1000 * 60 * 60 * 2;

export async function runOnce() {
  const client = await getClientAsync();
  const dbName = process.env.DB_NAME || 'sample_retail_12';
  const db = client.db(dbName);
  const carts = db.collection('carts');
  const customers = db.collection('customers');
  const notifications = db.collection('notifications');

  const cutoff = new Date(Date.now() - TWO_HOURS_MS);
  // find carts not notified and lastUpdated < cutoff
  const cursor = carts.find({ notified: { $ne: true }, lastUpdated: { $lt: cutoff } });

  const results = [];
  while (await cursor.hasNext()) {
    const cart = await cursor.next();
    const customer = await customers.findOne({ _id: cart.customerId });
    if (!customer) continue;

    // Generate message
    const message = await generateMessage({ customer, cart });

    // Choose channel
    const channel = customer.preferredChannel === 'sms' ? 'sms' : 'email';

    // Send (simulated)
    const sendResult = await sendNotification({ customer, channel, message });

    // Log notification
    const notif = {
      cartId: cart._id,
      customerId: customer._id,
      channel,
      message,
      status: sendResult.status,
      provider: sendResult.provider,
      providerId: sendResult.providerId,
      sentAt: new Date()
    };
    await notifications.insertOne(notif);

    // Mark cart notified
    await carts.updateOne({ _id: cart._id }, { $set: { notified: true, lastNotifiedAt: new Date() } });

    results.push({ cartId: cart._id, customerId: customer._id, notif });
  }

  return results;
}
