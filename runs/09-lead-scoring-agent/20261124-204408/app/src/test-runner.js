// Lightweight test runner used by `npm test` — verifies seed and scoring run paths
require('dotenv').config();
const { execSync } = require('child_process');

console.log('Running lightweight checks...');
try {
  execSync('node src/seed.js', { stdio: 'inherit' });
  execSync('node src/scoreLead.js --leadId=lead-1', { stdio: 'inherit' });
  console.log('Lightweight checks passed.');
} catch (e) {
  console.error('Lightweight checks failed:', e);
  process.exit(1);
}
