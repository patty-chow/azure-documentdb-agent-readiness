const Bed = require('./models/bed');
const WardSummary = require('./models/wardSummary');
const { mongoose } = require('./db');

// Handles change stream events: increment/decrement ward summary counts atomically
async function startChangeWatcher(timeoutMs = 15000) {
  console.log('Starting change stream watcher on Bed collection');
  const pipeline = [
    { $match: { 'operationType': { $in: ['insert', 'update', 'replace', 'delete'] } } }
  ];

  const changeStream = Bed.watch(pipeline, { fullDocument: 'updateLookup' });

  changeStream.on('change', async (change) => {
    try {
      // Determine previous and new status where possible
      // For insert/replace: use fullDocument
      // For update: fullDocument contains post-update state
      // For delete: documentKey/_id is present but fullDocument is null

      let wardId = null;
      let newStatus = null;
      let oldStatus = null;

      if (change.operationType === 'delete') {
        // We don't have the full document; ignore for summary or decrement if desired
        console.log('Delete event; documentKey:', change.documentKey);
        return;
      }

      const full = change.fullDocument;
      if (full) {
        wardId = full.wardId;
        newStatus = full.status;
      }

      // Try to get old status from updateDescription? Not always present. Use change.documentKey._id to fetch pre-image if needed; pre-image requires config.
      // Simpler approach: query the WardSummary by wardId and adjust counters conservatively by comparing with DB state.

      if (!wardId) {
        console.log('No wardId in change event; skipping');
        return;
      }

      // For demo simplicity: recompute counts for the affected ward atomically by reading counts from current Bed collection and setting summary
      const counts = { occupied: 0, available: 0, cleaning: 0 };
      const beds = await Bed.find({ wardId }).lean();
      for (const b of beds) counts[b.status] = (counts[b.status] || 0) + 1;

      await WardSummary.updateOne({ wardId }, { $set: { counts } }, { upsert: true });
      console.log(`Updated ward summary for ${wardId}:`, counts);
    } catch (err) {
      console.error('Error processing change event:', err);
    }
  });

  // Return a promise that resolves after timeoutMs and closes the change stream
  return new Promise((resolve) => {
    setTimeout(async () => {
      await changeStream.close();
      console.log('Change stream watcher stopped');
      resolve();
    }, timeoutMs);
  });
}

module.exports = { startChangeWatcher };
