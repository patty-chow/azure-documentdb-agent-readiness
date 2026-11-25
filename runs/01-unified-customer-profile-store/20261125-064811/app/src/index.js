const express = require('express');
require('dotenv').config();
const eventsRoute = require('./routes/events');
const dbModule = require('./db');

const app = express();
app.use(express.json());

app.use('/events', eventsRoute);

const PORT = process.env.PORT || 3000;

async function main() {
  await dbModule.connect();
  app.listen(PORT, () => {
    console.log(`Customer 360 sample listening on port ${PORT}`);
    console.log('POST events to /events with JSON { source, customerId, attributes }');
  });
}

main().catch(err => {
  console.error('Failed to start:', err.message);
  process.exit(1);
});
