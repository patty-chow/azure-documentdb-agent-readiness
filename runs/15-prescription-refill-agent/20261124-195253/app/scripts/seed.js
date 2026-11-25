const { connect, mongoose } = require('../src/db');
const PrescriptionSchema = require('../src/models/Prescription');
const RefillRequestSchema = require('../src/models/RefillRequest');

const Prescription = mongoose.model('Prescription', PrescriptionSchema);
const RefillRequest = mongoose.model('RefillRequest', RefillRequestSchema);

async function seed() {
  await connect();

  // Ensure indexes per sample design
  await Prescription.collection.createIndex({ patientId: 1, active: 1 });
  await Prescription.collection.createIndex({ prescriptionId: 1 }, { unique: true });
  await RefillRequest.collection.createIndex({ patientId: 1, requestedAt: -1 });

  // Upsert some sample patients/prescriptions
  const now = new Date();
  const days = (n) => new Date(now.getTime() - n * 24 * 60 * 60 * 1000);

  const samples = [
    {
      patientId: 'patient-1',
      prescriptionId: 'rx-1001',
      drugName: 'Lisinopril',
      daysSupply: 30,
      refillCount: 1,
      lastFilledAt: days(28), // 2 days remaining
      active: true
    },
    {
      patientId: 'patient-1',
      prescriptionId: 'rx-1002',
      drugName: 'Atorvastatin',
      daysSupply: 30,
      refillCount: 0,
      lastFilledAt: days(5),
      active: true
    },
    {
      patientId: 'patient-2',
      prescriptionId: 'rx-2001',
      drugName: 'Metformin',
      daysSupply: 90,
      refillCount: 2,
      lastFilledAt: days(85), // 5 days remaining -> not eligible
      active: true
    }
  ];

  for (const s of samples) {
    await Prescription.updateOne({ prescriptionId: s.prescriptionId }, { $set: s }, { upsert: true });
  }

  console.log('Seed complete.');
  process.exit(0);
}

seed().catch(err => { console.error(err); process.exit(1); });
