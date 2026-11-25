const dotenv = require('dotenv');
dotenv.config();

const { connect, mongoose } = require('../src/db');
const AuditEvent = require('../src/models/AuditEvent');

async function run(reference) {
  await connect();
  const timeline = await AuditEvent.getTimeline(reference);
  console.log(JSON.stringify(timeline, null, 2));
  await mongoose.connection.close();
}

if (require.main === module) {
  const ref = process.argv[2] || 'PAY-1001';
  run(ref).catch(err => {
    console.error(err);
    process.exit(1);
  });
}

module.exports = { run };
