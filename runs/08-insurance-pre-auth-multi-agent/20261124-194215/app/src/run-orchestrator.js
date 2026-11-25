#!/usr/bin/env node
require('dotenv').config();
const { processPreauth } = require('./orchestrator');

async function main(){
  const arg = process.argv[2];
  let id = null;
  if (arg && arg.startsWith('--id=')) id = arg.split('=')[1];
  else if (arg) id = arg;
  else id = process.env.PREAUTH_ID;

  if (!id){
    console.error('Usage: node src/run-orchestrator.js --id=<preauthId>');
    process.exit(2);
  }

  try{
    const res = await processPreauth(id);
    console.log('Done. Submission id created for preauth:', res.preauthId);
    process.exit(0);
  }catch(e){
    console.error('Error running orchestrator:', e);
    process.exit(1);
  }
}

if (require.main === module) main();
