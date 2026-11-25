const Heartbeat = require('../models/heartbeat');
const AtmStatus = require('../models/atmStatus');
const Summary = require('../models/summary');
const Alert = require('../models/alert');

async function recomputeSummary(threshold) {
  // Aggregate counts from atm_statuses
  const countsAgg = await AtmStatus.aggregate([
    { $group: { _id: '$status', count: { $sum: 1 } } }
  ]);
  const counts = { online: 0, offline: 0, low_cash: 0 };
  for (const r of countsAgg) {
    counts[r._id] = r.count;
  }
  const total = counts.online + counts.offline + counts.low_cash;
  const availability = total === 0 ? 1.0 : counts.online / total;

  const summaryDoc = await Summary.findOneAndUpdate(
    { _id: 'network_summary' },
    { $set: { counts, availability, lastUpdated: new Date() } },
    { upsert: true, new: true }
  );

  if (availability < threshold) {
    await Alert.create({ availability, threshold, reason: 'availability_below_threshold' });
  }

  return summaryDoc;
}

async function handleHeartbeat(hb, threshold) {
  // Upsert atm_statuses
  await AtmStatus.findOneAndUpdate(
    { atmId: hb.atmId },
    { $set: { status: hb.status, lastSeen: hb.timestamp || new Date() } },
    { upsert: true }
  );
  return recomputeSummary(threshold);
}

module.exports = { recomputeSummary, handleHeartbeat };
