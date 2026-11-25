const { connect } = require('../src/db');
const { checkEligibility } = require('../src/agent');
const Prescription = require('../src/models/prescription');

async function run() {
  await connect();
  const p = await Prescription.findOne({ prescriptionId: 'rx-1001' }).lean();
  if (!p) {
    console.error('Test data not found. Run npm run seed first.');
    process.exit(2);
  }
  const res = checkEligibility(p);
  console.log('Eligibility for', p.prescriptionId, res);
  process.exit(0);
}

run().catch(err => { console.error(err); process.exit(2); });
