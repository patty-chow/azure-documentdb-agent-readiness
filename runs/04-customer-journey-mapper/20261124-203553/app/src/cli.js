#!/usr/bin/env node
require('dotenv').config();
const minimist = require('minimist');
const { getCustomerJourney } = require('./aggregationTool');
const { summarizeJourney } = require('./agent');

async function main() {
  const argv = minimist(process.argv.slice(2));
  const customerId = argv.customer || argv.customerId || argv.c;
  if (!customerId) {
    console.error('Usage: node src/cli.js --customer <customerId>');
    process.exit(2);
  }
  try {
    const journey = await getCustomerJourney(customerId);
    const summary = await summarizeJourney(journey);
    console.log(JSON.stringify({ journey, summary }, null, 2));
  } catch (err) {
    console.error('Error:', err);
    process.exit(1);
  }
}

if (require.main === module) main();
