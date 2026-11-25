import dotenv from 'dotenv';
dotenv.config();
import { getDb, closeClient } from './db.js';
import { generateRecoveryMessage } from './copyAgent.js';
import { sendByPreference } from './channelAgent.js';

// Pipeline: find carts abandoned > 2 hours, generate message, send, log result
async function runOnce() {
  const db = await getDb();
  const carts = db.collection('carts');
  const customers = db.collection('customers');
  const logs = db.collection('recovery_logs');

  const cutoff = new Date(Date.now() - 2 * 60 * 60 * 1000);
  const cursor = carts.find({ abandonedAt: { $lte: cutoff } });

  let processed = 0;
  for await (const cart of cursor) {
    const customer = await customers.findOne({ customerId: cart.customerId });
    if (!customer) {
      console.warn('Missing customer for cart', cart.cartId);
      continue;
    }
    // Generate message
    let message;
    try {
      message = await generateRecoveryMessage(cart, customer);
    } catch (e) {
      console.error('Copy generation failed for', cart.cartId, e);
      await logs.insertOne({ cartId: cart.cartId, customerId: cart.customerId, status: 'copy_failed', error: String(e), timestamp: new Date() });
      continue;
    }
    // Send
    let sendResult;
    try {
      sendResult = await sendByPreference(customer, message);
    } catch (e) {
      console.error('Send failed for', cart.cartId, e);
      await logs.insertOne({ cartId: cart.cartId, customerId: cart.customerId, status: 'send_failed', error: String(e), message, timestamp: new Date() });
      continue;
    }
    // Log success
    await logs.insertOne({ cartId: cart.cartId, customerId: cart.customerId, status: 'sent', channelResult: sendResult, message, timestamp: new Date() });
    console.log('Processed cart', cart.cartId, '->', sendResult.provider || sendResult.channel || 'simulated');
    processed++;
  }

  await closeClient();
  console.log('Run complete. Processed', processed);
}

runOnce().catch(err => {
  console.error('Run failed', err);
  process.exit(1);
});
