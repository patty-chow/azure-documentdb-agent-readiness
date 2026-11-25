/* Short-lived watcher runner for manual testing: connects, starts watcher, runs for 10 seconds, then exits */
const AlertWatcher = require('../src/alert_watcher');

async function run() {
  await AlertWatcher.start();
  console.log('Watcher running for 10 seconds...');
  setTimeout(async () => {
    console.log('Stopping watcher');
    await AlertWatcher.stop();
    process.exit(0);
  }, 10000);
}

run().catch(err => { console.error(err); process.exit(1); });
