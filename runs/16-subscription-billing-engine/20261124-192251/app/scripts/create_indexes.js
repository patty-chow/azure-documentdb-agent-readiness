// Creates necessary indexes: unique idempotencyKey on ChargeEvent, TTL on Entitlement.expiresAt
const { connect, mongoose } = require('../src/db');
const ChargeEvent = require('../src/models/chargeEvent');
const Entitlement = require('../src/models/entitlement');

async function run() {
  await connect();
  console.log('Creating indexes...');
  try {
    await ChargeEvent.collection.createIndex({ idempotencyKey: 1 }, { unique: true, name: 'uniq_idempotencyKey' });
    console.log('Created unique index on ChargeEvent.idempotencyKey');
  } catch (e) {
    console.warn('Could not create unique index on ChargeEvent.idempotencyKey (maybe exists):', e.message);
  }

  try {
    await ChargeEvent.collection.createIndex({ customerId: 1 }, { name: 'idx_charge_customerId' });
    console.log('Created index on ChargeEvent.customerId');
  } catch (e) {
    console.warn('Could not create index on ChargeEvent.customerId:', e.message);
  }

  try {
    await Entitlement.collection.createIndex({ expiresAt: 1 }, { expireAfterSeconds: 0, name: 'ttl_entitlement_expiresAt' });
    console.log('Created TTL index on Entitlement.expiresAt');
  } catch (e) {
    console.warn('Could not create TTL index on Entitlement.expiresAt:', e.message);
  }

  console.log('Done');
  process.exit(0);
}

run().catch(err => { console.error(err); process.exit(1); });
