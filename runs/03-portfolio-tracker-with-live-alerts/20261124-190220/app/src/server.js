const app = require('./app');
const { connect, mongoose } = require('./db');
const PositionSchema = require('./models/position');
const AlertRuleSchema = require('./models/alertrule');
const AlertWatcher = require('./alert_watcher');

const PORT = process.env.PORT || 3000;

async function start() {
  await connect();
  // register models (this will also ensure indexes when Mongoose creates models)
  mongoose.model('Position', PositionSchema, 'positions');
  mongoose.model('AlertRule', AlertRuleSchema, 'alertrules');

  // start the alert watcher in background
  AlertWatcher.start();

  app.listen(PORT, () => {
    console.log(`Server listening on ${PORT}`);
  });
}

start().catch(err => {
  console.error('Failed to start', err);
  process.exit(1);
});
