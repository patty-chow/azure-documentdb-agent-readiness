const { getDb } = require('../db');

// Stubbed senders
async function sendEmail(to, subject, body) {
  // Simulate async send and return a delivery object
  console.log(`[sendEmail] to=${to} subject=${subject} body=${body}`);
  return { success: true, provider: 'stub-email', id: `email_${Date.now()}` };
}

async function sendSMS(to, body) {
  console.log(`[sendSMS] to=${to} body=${body}`);
  return { success: true, provider: 'stub-sms', id: `sms_${Date.now()}` };
}

async function sendAccordingToPreference(customer, message) {
  if (!customer) throw new Error('customer required');
  const contactPref = (customer.contactPreference || 'email').toLowerCase();
  if (contactPref === 'sms') {
    return await sendSMS(customer.phone, message);
  }
  return await sendEmail(customer.email, 'We miss you — items in your cart', message);
}

async function logDelivery(cartId, entry) {
  const db = await getDb();
  const carts = db.collection('carts');
  await carts.updateOne({ cartId }, { $push: { deliveryLog: entry }, $set: { processedAt: new Date() } });
}

module.exports = { sendAccordingToPreference, logDelivery };
