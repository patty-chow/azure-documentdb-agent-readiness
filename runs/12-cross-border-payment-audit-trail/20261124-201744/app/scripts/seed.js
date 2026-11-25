const dotenv = require('dotenv');
dotenv.config();

const { connect, mongoose } = require('../src/db');
const AuditEvent = require('../src/models/AuditEvent');

async function seed() {
  await connect();

  const samples = [
    {
      paymentReference: 'PAY-1001',
      stage: 'initiated',
      stageTimestamp: new Date('2026-01-01T10:00:00Z'),
      details: { amount: 1000, currency: 'USD', from: 'A', to: 'B' }
    },
    {
      paymentReference: 'PAY-1001',
      stage: 'routed',
      stageTimestamp: new Date('2026-01-01T10:05:00Z'),
      details: { route: ['bankA', 'bankB'] }
    },
    {
      paymentReference: 'PAY-1001',
      stage: 'fx_converted',
      stageTimestamp: new Date('2026-01-01T10:06:00Z'),
      details: { fromCurrency: 'USD', toCurrency: 'EUR', rate: 0.92 }
    },
    {
      paymentReference: 'PAY-1001',
      stage: 'settled',
      stageTimestamp: new Date('2026-01-01T10:20:00Z'),
      details: { settledAt: '2026-01-01T10:20:00Z' }
    }
  ];

  for (const ev of samples) {
    const id = `${ev.paymentReference}_${ev.stage}`;
    const exists = await AuditEvent.findById(id).lean().exec();
    if (exists) {
      console.log(`Skipping existing ${id}`);
      continue;
    }
    const doc = new AuditEvent({ _id: id, ...ev });
    await doc.save();
    console.log(`Inserted ${id}`);
  }

  await mongoose.connection.close();
}

seed().catch(err => {
  console.error(err);
  process.exit(1);
});
