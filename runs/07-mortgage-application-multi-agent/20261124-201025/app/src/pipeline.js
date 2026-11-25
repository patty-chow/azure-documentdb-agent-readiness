const { getDb } = require('./db');
const underwriting = require('./agents/underwriting');
const compliance = require('./agents/compliance');
const comms = require('./agents/comms');

async function runForApplication(applicationId) {
  const db = await getDb();
  const apps = db.collection('applications');
  const decisions = db.collection('decisions');

  const app = await apps.findOne({ applicationId });
  if (!app) throw new Error(`Application ${applicationId} not found`);

  const uw = await underwriting.assess(app);
  const comp = await compliance.check(app);
  const letter = await comms.draft(app, uw, comp);

  const decisionDoc = {
    applicationId,
    timestamp: new Date(),
    underwriting: uw,
    compliance: comp,
    letter,
  };

  await decisions.updateOne({ applicationId }, { $set: decisionDoc }, { upsert: true });
  return decisionDoc;
}

module.exports = { runForApplication };
