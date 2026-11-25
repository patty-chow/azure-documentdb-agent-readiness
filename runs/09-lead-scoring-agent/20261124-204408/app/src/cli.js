#!/usr/bin/env node
const argv = require('minimist')(process.argv.slice(2));
const { scoreLead } = require('./agent');

async function main() {
  const leadId = argv.leadId || argv.lead || argv._[0];
  if (!leadId) {
    console.error('Usage: node src/cli.js --leadId=lead-1');
    process.exit(2);
  }
  try {
    const res = await scoreLead(leadId);
    console.log(JSON.stringify(res, null, 2));
    process.exit(0);
  } catch (err) {
    console.error('Error scoring lead:', err);
    process.exit(1);
  }
}
main();
