const dotenv = require('dotenv');
dotenv.config();

const { connect, mongoose } = require('../src/db');
const AuditEvent = require('../src/models/AuditEvent');

async function verify() {
  await connect();
  const id = 'PAY-1001_initiated';

  console.log('Attempting updateOne (should be rejected)...');
  try {
    await AuditEvent.updateOne({ _id: id }, { $set: { 'details.rejected': true } });
    console.error('ERROR: updateOne did not throw as expected');
    process.exitCode = 2;
  } catch (err) {
    console.log('updateOne rejected as expected:', err.message);
  }

  console.log('Attempting findOneAndUpdate (should be rejected)...');
  try {
    await AuditEvent.findOneAndUpdate({ _id: id }, { $set: { 'details.rejected2': true } }, { new: true });
    console.error('ERROR: findOneAndUpdate did not throw as expected');
    process.exitCode = 2;
  } catch (err) {
    console.log('findOneAndUpdate rejected as expected:', err.message);
  }

  console.log('Attempting to save existing document via save() (should be rejected)...');
  try {
    const doc = await AuditEvent.findById(id).exec();
    doc.details.foo = 'bar';
    await doc.save();
    console.error('ERROR: save() on existing doc did not throw as expected');
    process.exitCode = 2;
  } catch (err) {
    console.log('save() rejected as expected:', err.message);
  }

  await mongoose.connection.close();
}

verify().catch(err => {
  console.error('Verification script failed:', err);
  process.exit(1);
});
