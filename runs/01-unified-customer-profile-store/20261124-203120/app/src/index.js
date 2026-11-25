const express = require('express');
const { connect, mongoose } = require('./db');
const CustomerProfileSchema = require('./models/customerProfile');

const app = express();
app.use(express.json());

async function start() {
  await connect();
  const CustomerProfile = mongoose.model('CustomerProfile', CustomerProfileSchema);

  // ensure indexes exist (safe on repeated runs)
  await CustomerProfile.syncIndexes();

  const eventsRouter = require('./routes/events')(CustomerProfile);
  app.use('/events', eventsRouter);

  const port = process.env.PORT || 3000;
  app.listen(port, () => console.log(`Customer360 sample listening on ${port}`));
}

if (require.main === module) {
  start().catch(err => {
    console.error('Failed to start:', err.message);
    process.exit(1);
  });
}

module.exports = app;
