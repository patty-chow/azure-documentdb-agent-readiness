// Demo script: fetch and print a customer's timeline length and channels without calling the LLM.
require('dotenv').config();
const { getCustomerJourney } = require('../src/aggregationTool');

async function main() {
  const customerId = process.argv[2] || 'cust_0001';
  const journey = await getCustomerJourney(customerId);
  console.log(`Customer ${customerId} timeline length: ${journey.timeline.length}`);
  console.log('Channels and counts:');
  for (const [ch, arr] of Object.entries(journey.byChannel)) {
    console.log(` - ${ch}: ${arr.length}`);
  }
}

main().catch(err => {
  console.error(err);
  process.exit(1);
});
