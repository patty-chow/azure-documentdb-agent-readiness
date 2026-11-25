#!/usr/bin/env node
const { getClient, getDb } = require('./db');

async function seed() {
  const client = await getClient();
  const db = await getDb();

  const slots = db.collection('slots');
  const appointments = db.collection('appointments');

  // create compound index: providerId, start, status
  await slots.createIndex({ providerId: 1, start: 1, status: 1 }, { name: 'provider_start_status_idx' });
  // index appointment by patientId
  await appointments.createIndex({ patientId: 1, createdAt: -1 }, { name: 'patient_createdAt_idx' });

  // Upsert sample providers/slots
  const providerId = 'provider_1';
  const now = new Date();

  const makeISO = (d) => d.toISOString();

  const slotDocs = [];
  for (let i = 1; i <= 5; i++) {
    const start = new Date(now.getTime() + i * 60 * 60 * 1000); // next hours
    const end = new Date(start.getTime() + 30 * 60 * 1000); // 30 min
    const id = `${providerId}_${makeISO(start)}`;
    slotDocs.push({
      _id: id,
      providerId,
      start,
      end,
      status: 'available',
      metadata: { room: `Room ${i}` }
    });
  }

  for (const s of slotDocs) {
    await slots.updateOne({ _id: s._id }, { $set: s }, { upsert: true });
  }

  // Create one appointment occupying the second slot
  const bookedSlot = slotDocs[1];
  const apptId = 'appt_1';
  await appointments.updateOne(
    { _id: apptId },
    { $set: { _id: apptId, patientId: 'patient_1', slotId: bookedSlot._id, status: 'booked', createdAt: new Date(), notes: 'Initial booking' } },
    { upsert: true }
  );

  // Mark the booked slot as booked
  await slots.updateOne({ _id: bookedSlot._id }, { $set: { status: 'booked' } });

  console.log('Seeding complete. Inserted slots:', slotDocs.length, 'and 1 appointment.');
  await client.close();
}

seed().catch(err => { console.error(err); process.exitCode = 1; });
