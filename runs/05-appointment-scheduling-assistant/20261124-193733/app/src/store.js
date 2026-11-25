const { getClient, getDb } = require('./db');

async function findAvailableSlots(providerId, from, to, limit=10) {
  const db = await getDb();
  const q = { providerId, status: 'available' };
  if (from || to) q.start = {};
  if (from) q.start.$gte = from;
  if (to) q.start.$lte = to;
  return db.collection('slots').find(q).sort({ start: 1 }).limit(limit).toArray();
}

async function createAppointmentAtomic(patientId, slotId, notes='') {
  const client = await getClient();
  const session = client.startSession();
  const db = await getDb();
  try {
    let result;
    await session.withTransaction(async () => {
      const slots = db.collection('slots');
      const appointments = db.collection('appointments');

      // Reserve slot only if it's available
      const slot = await slots.findOneAndUpdate(
        { _id: slotId, status: 'available' },
        { $set: { status: 'booked' } },
        { session, returnDocument: 'after' }
      );

      if (!slot.value) {
        throw new Error('Slot not available');
      }

      const appt = { _id: `appt_${Date.now()}`, patientId, slotId, status: 'booked', createdAt: new Date(), notes };
      await appointments.insertOne(appt, { session });
      result = appt;
    });
    return result;
  } finally {
    await session.endSession();
  }
}

async function cancelAppointment(appointmentId) {
  const client = await getClient();
  const session = client.startSession();
  const db = await getDb();
  try {
    let result;
    await session.withTransaction(async () => {
      const appts = db.collection('appointments');
      const slots = db.collection('slots');

      const appt = await appts.findOne({ _id: appointmentId }, { session });
      if (!appt) throw new Error('Appointment not found');

      await appts.updateOne({ _id: appointmentId }, { $set: { status: 'cancelled' } }, { session });
      await slots.updateOne({ _id: appt.slotId }, { $set: { status: 'available' } }, { session });
      result = { appointmentId, cancelled: true };
    });
    return result;
  } finally {
    await session.endSession();
  }
}

async function rescheduleAppointmentAtomic(appointmentId, targetSlotId) {
  const client = await getClient();
  const session = client.startSession();
  const db = await getDb();
  try {
    let result;
    await session.withTransaction(async () => {
      const appts = db.collection('appointments');
      const slots = db.collection('slots');

      const appt = await appts.findOne({ _id: appointmentId }, { session });
      if (!appt) throw new Error('Appointment not found');

      // Try to mark target slot booked
      const newSlot = await slots.findOneAndUpdate(
        { _id: targetSlotId, status: 'available' },
        { $set: { status: 'booked' } },
        { session, returnDocument: 'after' }
      );
      if (!newSlot.value) throw new Error('Target slot not available');

      // Free old slot
      await slots.updateOne({ _id: appt.slotId }, { $set: { status: 'available' } }, { session });

      // Update appointment
      await appts.updateOne({ _id: appointmentId }, { $set: { slotId: targetSlotId, status: 'booked' } }, { session });

      result = { appointmentId, newSlotId: targetSlotId };
    });
    return result;
  } finally {
    await session.endSession();
  }
}

module.exports = { findAvailableSlots, createAppointmentAtomic, cancelAppointment, rescheduleAppointmentAtomic };
