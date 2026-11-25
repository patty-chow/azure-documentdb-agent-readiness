// Demo script: simulate an initial refill request that names the drug, then a follow-up without the drug name
const { connect } = require('../src/db');
const { handleMessage, memory } = require('../src/agent');

async function run() {
  await connect();
  const sessionId = 'demo-session-1';
  const patientId = 'patient-1';

  console.log('--- Initial message: "Refill Lisinopril 10mg"');
  let res = await handleMessage({ sessionId, patientId, message: 'Refill Lisinopril 10mg' });
  console.log('Agent reply:', res.reply);
  if (res.refillRequest) console.log('Created refillRequest id:', res.refillRequest._id);

  console.log('\n--- Follow-up message: "refill my blood pressure medication"');
  res = await handleMessage({ sessionId, patientId, message: 'refill my blood pressure medication' });
  console.log('Agent reply:', res.reply);
  if (res.refillRequest) console.log('Created refillRequest id:', res.refillRequest._id);

  process.exit(0);
}

run().catch(err => { console.error(err); process.exit(2); });
