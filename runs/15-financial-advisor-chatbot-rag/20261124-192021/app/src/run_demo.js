const seed = require('./seed');
const { answerQuery } = require('./agent');

async function run() {
  console.log('Running end-to-end demo...');

  // Seed (idempotent)
  console.log('Seeding data...');
  await seed();

  const session = 'demo-session-1';

  const q1 = 'Give me a summary of municipal bonds and how they fit into a taxable portfolio.';
  console.log('\n> User:', q1);
  const r1 = await answerQuery(session, q1);
  console.log('\nAssistant:\n', r1.text);

  const q2 = 'How does that affect my bond allocation?';
  console.log('\n> User (follow-up):', q2);
  const r2 = await answerQuery(session, q2);
  console.log('\nAssistant (follow-up):\n', r2.text);

  console.log('\nDemo complete — top-cited article IDs from first turn:', r1.retrieved.map(r=>r._id).join(', '));
}

run().catch(err => {
  console.error(err);
  process.exit(1);
});
