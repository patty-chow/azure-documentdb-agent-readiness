require('dotenv').config();
const { connect } = require('../src/db');
const Interaction = require('../src/models/interaction');

async function normalize(a,b) {
  const parts = [String(a).trim().toLowerCase(), String(b).trim().toLowerCase()].sort();
  return parts.join('|');
}

async function seed() {
  await connect();

  const samples = [
    { drugA: 'warfarin', drugB: 'aspirin', severityScore: 8, clinicalRecommendation: 'Avoid combination if possible; monitor INR closely', evidence: ['Increased bleeding risk when combined; aspirin potentiates warfarin effect.'] },
    { drugA: 'ibuprofen', drugB: 'aspirin', severityScore: 4, clinicalRecommendation: 'Concurrent use may reduce cardioprotective effect of low-dose aspirin; consider spacing dosing', evidence: ['NSAIDs may interfere with aspirin platelet inhibition.'] },
    { drugA: 'metformin', drugB: 'contrast dye', severityScore: 6, clinicalRecommendation: 'Hold metformin around contrast administration in patients with reduced renal function', evidence: ['Risk of lactic acidosis in renal impairment after contrast.'] },
    { drugA: 'lisinopril', drugB: 'spironolactone', severityScore: 7, clinicalRecommendation: 'Monitor potassium and renal function; risk of hyperkalemia', evidence: ['ACE inhibitors + aldosterone antagonists increase hyperkalemia risk.'] },
    { drugA: 'simvastatin', drugB: 'clarithromycin', severityScore: 9, clinicalRecommendation: 'Avoid co-administration; clarithromycin increases statin levels leading to myopathy', evidence: ['CYP3A4 inhibition increases simvastatin exposure.'] },
    { drugA: 'sertraline', drugB: 'sumatriptan', severityScore: 6, clinicalRecommendation: 'Use caution due to serotonin syndrome risk', evidence: ['Serotonergic agents combined may increase serotonin syndrome risk.'] },
    { drugA: 'digoxin', drugB: 'verapamil', severityScore: 6, clinicalRecommendation: 'Monitor digoxin levels and signs of toxicity', evidence: ['Verapamil can increase digoxin levels.'] },
    { drugA: 'warfarin', drugB: 'metronidazole', severityScore: 7, clinicalRecommendation: 'Monitor INR; consider alternative antibiotics', evidence: ['Metronidazole potentiates warfarin anticoagulation.'] },
    { drugA: 'aspirin', drugB: 'ibuprofen', severityScore: 4, clinicalRecommendation: 'See ibuprofen/aspirin note', evidence: ['Duplicate entry for demonstration.'] },
    { drugA: 'fluoxetine', drugB: 'tamoxifen', severityScore: 5, clinicalRecommendation: 'Consider alternative SSRI due to reduced tamoxifen activation', evidence: ['Fluoxetine inhibits CYP2D6 reducing tamoxifen effectiveness.'] },
    { drugA: 'acetaminophen', drugB: 'warfarin', severityScore: 3, clinicalRecommendation: 'Monitor INR with frequent acetaminophen use', evidence: ['High-dose or chronic acetaminophen may increase INR.'] },
    { drugA: 'amiodarone', drugB: 'warfarin', severityScore: 8, clinicalRecommendation: 'Lower warfarin dose and monitor INR when starting/stopping amiodarone', evidence: ['Amiodarone potentiates warfarin effect leading to bleeding.'] }
  ];

  for (const s of samples) {
    const normalizedPair = await normalize(s.drugA, s.drugB);
    const doc = {
      drugA: String(s.drugA).trim().toLowerCase(),
      drugB: String(s.drugB).trim().toLowerCase(),
      normalizedPair,
      severityScore: s.severityScore,
      clinicalRecommendation: s.clinicalRecommendation,
      evidence: s.evidence,
      updatedAt: new Date()
    };
    await Interaction.updateOne({ normalizedPair }, { $set: doc }, { upsert: true });
    console.log('Upserted', normalizedPair);
  }
  console.log('Seeding complete');
  process.exit(0);
}

seed().catch(err => { console.error(err); process.exit(1); });
