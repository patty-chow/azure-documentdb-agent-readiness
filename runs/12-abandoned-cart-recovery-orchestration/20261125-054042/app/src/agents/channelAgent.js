// Simulated channel agent: choose SMS or Email and simulate sending.
// Real provider integration points are documented in README and .env.example

class ChannelAgent {
  constructor() {
    // Could initialize real SDKs (Twilio/SendGrid) if creds provided
    this.simulate = true;
  }

  async send(customer, message) {
    const channel = (customer.preferredChannel || 'email').toLowerCase();
    if (channel === 'sms') {
      return this.sendSms(customer, message);
    } else {
      return this.sendEmail(customer, message);
    }
  }

  async sendSms(customer, message) {
    // Simulate an SMS send; if TWILIO_ env vars provided, real SDK could be wired here
    console.log(`[channelAgent] Sending SMS to ${customer.phone}: ${message}`);
    return { ok: true, provider: 'simulated-sms' };
  }

  async sendEmail(customer, message) {
    console.log(`[channelAgent] Sending Email to ${customer.email}: ${message}`);
    return { ok: true, provider: 'simulated-email' };
  }
}

module.exports = ChannelAgent;
