const { connect, mongoose } = require('../src/db');
const PositionSchema = require('../src/models/position');
const AlertRuleSchema = require('../src/models/alertrule');

async function run() {
  await connect();
  const Position = mongoose.model('Position', PositionSchema, 'positions');
  const AlertRule = mongoose.model('AlertRule', AlertRuleSchema, 'alertrules');

  await Position.createIndexes();
  await AlertRule.createIndexes();
  console.log('Indexes created');
  process.exit(0);
}

run().catch(err=>{console.error(err); process.exit(1)});
