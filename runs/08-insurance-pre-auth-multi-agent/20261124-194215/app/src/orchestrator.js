require('dotenv').config();
const { getDb } = require('./db');
const { medicalReview } = require('./agents/medicalReviewAgent');
const { draftSubmission } = require('./agents/insurerCommsAgent');

async function processPreauth(preauthId){
  if (!preauthId) throw new Error('preauthId required');
  const db = await getDb();
  const preauthColl = db.collection('preauth_requests');
  const submissions = db.collection('submissions');

  const preauth = await preauthColl.findOne({ _id: preauthId });
  if (!preauth) throw new Error('Preauth not found: ' + preauthId);

  console.log('Loaded preauth:', preauthId);

  // Run medical review
  const assessment = await medicalReview(preauth);
  console.log('Assessment:', assessment);

  // Draft submission
  const letter = await draftSubmission(preauth, assessment);
  console.log('Drafted submission document (truncated):', letter.slice(0,200));

  // Persist submission
  const submissionDoc = {
    preauthId: preauth._id,
    submissionDocument: letter,
    outcome: assessment.necessary ? 'approved' : 'denied',
    assessment,
    submittedAt: new Date()
  };

  await submissions.insertOne(submissionDoc);
  await preauthColl.updateOne({ _id: preauth._id }, { $set: { status: 'submitted', lastSubmissionAt: new Date() } });

  console.log('Submission stored and preauth updated.');
  return submissionDoc;
}

module.exports = { processPreauth };
