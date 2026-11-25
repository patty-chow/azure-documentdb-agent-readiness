import dotenv from 'dotenv';
dotenv.config();

// This module implements pluggable adapters. If provider credentials are missing, it simulates sends.
import fetch from 'node-fetch';

export async function sendByPreference(customer, message) {
  const pref = customer.contactPreference || 'email';
  if (pref === 'sms') {
    return sendSms(customer.phone, message);
  }
  return sendEmail(customer.email, message);
}

async function sendEmail(to, message) {
  const sendgridKey = process.env.SENDGRID_API_KEY;
  if (!sendgridKey) {
    console.log(`[Simulated Email] To: ${to}\n${message}`);
    return { provider: 'simulated', channel: 'email', to };
  }
  // Basic SendGrid sending (simplified) -- do not embed key
  const res = await fetch('https://api.sendgrid.com/v3/mail/send', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${sendgridKey}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      personalizations: [{ to: [{ email: to }] }],
      from: { email: 'no-reply@example.com' },
      subject: 'We saved your cart!',
      content: [{ type: 'text/plain', value: message }]
    })
  });
  return { provider: 'sendgrid', ok: res.ok, status: res.status };
}

async function sendSms(to, message) {
  const sid = process.env.TWILIO_ACCOUNT_SID;
  const token = process.env.TWILIO_AUTH_TOKEN;
  const from = process.env.TWILIO_FROM_NUMBER;
  if (!sid || !token || !from) {
    console.log(`[Simulated SMS] To: ${to}\n${message}`);
    return { provider: 'simulated', channel: 'sms', to };
  }
  // Do a simple Twilio API call
  const auth = Buffer.from(`${sid}:${token}`).toString('base64');
  const params = new URLSearchParams();
  params.append('From', from);
  params.append('To', to);
  params.append('Body', message);
  const res = await fetch(`https://api.twilio.com/2010-04-01/Accounts/${sid}/Messages.json`, {
    method: 'POST',
    headers: {
      'Authorization': `Basic ${auth}`,
      'Content-Type': 'application/x-www-form-urlencoded'
    },
    body: params.toString()
  });
  return { provider: 'twilio', ok: res.ok, status: res.status };
}
