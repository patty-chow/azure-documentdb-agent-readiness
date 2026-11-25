require('dotenv').config();
const { getDb, getClient } = require('./db');

async function seed(){
  const client = await getClient();
  const db = await getDb();

  const preauth = db.collection('preauth_requests');
  const criteria = db.collection('clinical_criteria');
  const submissions = db.collection('submissions');

  // Create indexes (id's are implicit). Add patientId and status indexes, and text index on criteria.
  await preauth.createIndex({ patientId: 1 });
  await preauth.createIndex({ status: 1 });
  await criteria.createIndex({ criteriaText: 'text' });
  await submissions.createIndex({ preauthId: 1 });

  // Seed sample clinical criteria (upsert by procedureCode)
  const sampleCriteria = [
    { procedureCode: 'PROC-100', criteriaText: 'Procedure PROC-100 requires evidence of prior conservative therapy for 6 weeks.', severityTags: ['moderate'] },
    { procedureCode: 'PROC-200', criteriaText: 'Procedure PROC-200 is indicated for acute severe presentations with imaging confirmation.', severityTags: ['severe'] },
    { procedureCode: 'PROC-300', criteriaText: 'Procedure PROC-300 is elective and requires prior authorization and supporting notes.', severityTags: ['elective'] },
    { procedureCode: 'PROC-400', criteriaText: 'Procedure PROC-400 typically denied unless experimental protocol documented.', severityTags: ['experimental'] }
  ];

  for (const c of sampleCriteria){
    await criteria.updateOne({ procedureCode: c.procedureCode }, { $set: c }, { upsert: true });
  }

  // Seed sample preauth requests (non-PHI sample)
  const samplePreauth = [
    { _id: 'preauth-1', patientId: 'patient-1', clinician: 'Dr. Alice', requestedProcedureCodes: ['PROC-100'], clinicalNotes: 'Patient has tried PT for 8 weeks with minimal benefit.', submittedAt: new Date(), status: 'pending' },
    { _id: 'preauth-2', patientId: 'patient-2', clinician: 'Dr. Bob', requestedProcedureCodes: ['PROC-200'], clinicalNotes: 'Acute onset with MRI showing pathology.', submittedAt: new Date(), status: 'pending' },
    { _id: 'preauth-3', patientId: 'patient-3', clinician: 'Dr. Carol', requestedProcedureCodes: ['PROC-400'], clinicalNotes: 'Enrolled in experimental protocol.', submittedAt: new Date(), status: 'pending' }
  ];

  for (const p of samplePreauth){
    await preauth.updateOne({ _id: p._id }, { $set: p }, { upsert: true });
  }

  console.log('Seeding completed.');
  await client.close();
}

if (require.main === module){
  seed().catch(err=>{
    console.error('Seed failed:', err);
    process.exit(1);
  });
}

module.exports = { seed };
