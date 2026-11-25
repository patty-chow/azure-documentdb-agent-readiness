const { getClient, getDb } = require('./db');
const store = require('./store');

async function run() {
  console.log('Finding available slots for provider_1...');
  const now = new Date();
  const later = new Date(now.getTime() + 6 * 60 * 60 * 1000);
  const slots = await store.findAvailableSlots('provider_1', now, later);
  console.log('Available slots count:', slots.length);
  if (slots.length === 0) {
    console.log('No available slots to test with. Exiting.');
    process.exit(1);
  }

  const slotToBook = slots[0];
  console.log('Attempting to create appointment on slot', slotToBook._id);
  try {
    const appt = await store.createAppointmentAtomic('patient_demo', slotToBook._id, 'Demo booking');
    console.log('Created appointment:', appt);

    // Now try rescheduling to next available slot
    const remaining = await store.findAvailableSlots('provider_1', now, later);
    const target = remaining.find(s => s._id !== slotToBook._id);
    if (target) {
      console.log('Rescheduling appointment', appt._id, 'to', target._id);
      const res = await store.rescheduleAppointmentAtomic(appt._id, target._id);
      console.log('Reschedule result:', res);

      console.log('Cancelling appointment', appt._id);
      const cancelRes = await store.cancelAppointment(appt._id);
      console.log('Cancel result:', cancelRes);
    } else {
      console.log('No alternative slot available for reschedule test.');
    }
  } catch (e) {
    console.error('Error during demo verification:', e);
  } finally {
    const client = await getClient();
    await client.close();
  }
}

run().catch(err => { console.error(err); process.exitCode = 1; });
