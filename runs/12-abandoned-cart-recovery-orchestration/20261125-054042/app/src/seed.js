import { getDb, closeClient } from './db.js';

// idempotent seed: uses a test_marker to avoid duplicating repeated runs
const TEST_MARKER = 'sample12-abandoned-cart';

async function ensureIndexSafe(coll, indexSpec, options) {
  try {
    await coll.createIndex(indexSpec, options);
  } catch (e) {
    // If unique index creation failed due to existing duplicates, fall back
    if (e && e.code === 11000) {
      console.warn('Unique index creation failed (duplicates present). Falling back to non-unique index for', JSON.stringify(indexSpec));
      const opts = Object.assign({}, options);
      if (opts.unique) delete opts.unique;
      try {
        await coll.createIndex(indexSpec, opts);
      } catch (err) {
        console.error('Failed to create fallback index', err);
      }
    } else {
      console.warn('Index creation warning', e?.message || e);
    }
  }
}

async function safeUpsert(coll, filter, doc) {
  try {
    await coll.updateOne(filter, { $set: doc }, { upsert: true });
  } catch (e) {
    if (e && e.code === 11000) {
      console.warn('Upsert skipped due to duplicate key for filter', filter, 'doc', doc);
      return;
    }
    throw e;
  }
}

async function seed() {
  const db = await getDb();

  // collections
  const customers = db.collection('customers');
  const carts = db.collection('carts');
  const logs = db.collection('recovery_logs');

  // indexes: ensure abandonedAt is indexed for queries; customer preference index for lookups
  await ensureIndexSafe(carts, { abandonedAt: 1 }, {});
  await ensureIndexSafe(customers, { customerId: 1 }, { unique: true });
  await ensureIndexSafe(customers, { contactPreference: 1 }, {});
  await ensureIndexSafe(logs, { cartId: 1 }, {});

  // upsert a few customers and carts
  const now = new Date();
  const twoHoursAgo = new Date(now.getTime() - 2.5 * 60 * 60 * 1000); // 2.5 hours ago
  const oneHourAgo = new Date(now.getTime() - 60 * 60 * 1000);

  const sampleCustomers = [
    { customerId: 'cust-001', name: 'Alice', email: 'alice+sample12@example.com', phone: '+15550001', contactPreference: 'email', testMarker: TEST_MARKER },
    { customerId: 'cust-002', name: 'Bob', email: 'bob+sample12@example.com', phone: '+15550002', contactPreference: 'sms', testMarker: TEST_MARKER },
    { customerId: 'cust-003', name: 'Carol', email: 'carol+sample12@example.com', phone: '+15550003', contactPreference: 'email', testMarker: TEST_MARKER }
  ];

  for (const c of sampleCustomers) {
    await safeUpsert(customers, { customerId: c.customerId }, c);
  }

  const sampleCarts = [
    { cartId: 'cart-001', customerId: 'cust-001', items: [{ sku: 'SKU-1', name: 'Widget', qty: 1 }], abandonedAt: twoHoursAgo, total: 19.99, testMarker: TEST_MARKER },
    { cartId: 'cart-002', customerId: 'cust-002', items: [{ sku: 'SKU-2', name: 'Gadget', qty: 2 }], abandonedAt: twoHoursAgo, total: 39.98, testMarker: TEST_MARKER },
    { cartId: 'cart-003', customerId: 'cust-003', items: [{ sku: 'SKU-3', name: 'Thingamajig', qty: 1 }], abandonedAt: oneHourAgo, total: 9.99, testMarker: TEST_MARKER }
  ];

  for (const cart of sampleCarts) {
    await safeUpsert(carts, { cartId: cart.cartId }, cart);
  }

  console.log('Seed completed.');
  await closeClient();
}

seed().catch(err => {
  console.error('Seed failed', err);
  process.exit(1);
});
