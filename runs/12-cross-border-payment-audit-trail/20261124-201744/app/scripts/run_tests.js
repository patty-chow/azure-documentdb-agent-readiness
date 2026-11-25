// Lightweight verification script used by `npm test` to run seed + timeline using the live cluster.
const { execSync } = require('child_process');
try {
  console.log('Running seed...');
  execSync('node scripts/seed.js', { stdio: 'inherit' });
  console.log('\nRunning timeline query...');
  execSync('node scripts/query_timeline.js', { stdio: 'inherit' });
  console.log('\nTests completed.');
} catch (err) {
  console.error('Test run failed:', err.message);
  process.exit(1);
}
