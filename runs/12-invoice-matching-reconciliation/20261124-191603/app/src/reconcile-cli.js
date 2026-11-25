import dotenv from 'dotenv';
import { connect, disconnect } from './db.js';
import { runReconcile } from './reconciler.js';

dotenv.config();

async function main(){
  try {
    await connect();
    console.log('Running reconciliation (one-shot)...');
    const results = await runReconcile({ useLLM: !!process.env.OPENAI_API_KEY, limit: 50 });
    console.log('Results:', JSON.stringify(results, null, 2));
  } catch (e) {
    console.error('Error during reconcile:', e);
  } finally {
    await disconnect();
  }
}

main();
