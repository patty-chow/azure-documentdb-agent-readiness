// Simple smoke tests that try to run seed and run-once in offline-safe ways.
const { execSync } = require('child_process');

function run(cmd) {
  console.log('> ' + cmd);
  try {
    const out = execSync(cmd, { stdio: 'inherit' });
    return true;
  } catch (err) {
    console.error('Cmd failed', cmd, err && err.message);
    return false;
  }
}

// Run seed
if (!run('node src/seed.js')) process.exit(1);

// Run run-once
if (!run('node src/run_once.js')) process.exit(1);

console.log('Smoke run completed.');
