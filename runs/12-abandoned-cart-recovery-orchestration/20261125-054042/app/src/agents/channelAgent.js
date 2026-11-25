// Simulated channel agent. In production you would wire Twilio/SendGrid etc.
// This module exports a send function that either simulates or (optionally)
// calls a provider when credentials are provided. For safety, the sample
// defaults to simulation only.

export async function sendNotification({ customer, channel, message }) {
  // channel: 'email' | 'sms'
  // If a real provider is configured (TWILIO_* or SENDGRID_API_KEY) you
  // could implement real sends here. For the sample we simulate delivery.
  console.log(`Simulated send to ${channel} for customer ${customer._id}: ${message}`);
  return {
    status: 'ok',
    provider: 'simulator',
    providerId: `sim-${Date.now()}`
  };
}
