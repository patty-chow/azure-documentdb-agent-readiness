const { fetchEvidence } = require('./agents/evidenceAgent');
const { reasonPolicy } = require('./agents/policyAgent');
const { recordDecision } = require('./agents/decisionAgent');

async function orchestrateClaim(claimId) {
  const evidence = await fetchEvidence(claimId);
  const policy = await reasonPolicy(evidence);
  const decision = await recordDecision(claimId, policy.recommendation, policy.rationale || JSON.stringify(policy));
  return { evidence, policy, decision };
}

module.exports = { orchestrateClaim };
