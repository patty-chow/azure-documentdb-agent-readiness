const { createModel } = require('../models/customer');

async function upsertEvent(db, event) {
  // event: { source, customerId, attributes }
  const Customer = createModel(db);
  const { source, customerId, attributes } = event;
  if (!source || !customerId || typeof attributes !== 'object') {
    throw new Error('Invalid event shape; require source, customerId, attributes');
  }

  const filter = { customerId };
  const setPath = `sources.${source}`;
  const update = {
    $set: {
      [setPath]: attributes,
      updatedAt: new Date()
    },
    $setOnInsert: {
      customerId,
      createdAt: new Date()
    }
  };
  const opts = { upsert: true };

  const res = await Customer.updateOne(filter, update, opts);
  return res;
}

module.exports = { upsertEvent };
