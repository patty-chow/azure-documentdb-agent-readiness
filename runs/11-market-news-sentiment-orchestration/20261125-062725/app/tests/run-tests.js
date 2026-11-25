// Basic smoke tests for syntax and simple functions. These tests do not connect to remote cluster.
const { fetchHeadlines } = require('../src/scraper');
const { analyzeHeadlineLLM } = require('../src/ai');

async function smoke(){
  const h = await fetchHeadlines();
  console.log('fetchHeadlines returned', h.length, 'items');
  const a = await analyzeHeadlineLLM('AAPL reports record iPhone sales, shares jump');
  console.log('analysis', a);
}

smoke().then(()=>process.exit(0)).catch(e=>{ console.error(e); process.exit(2); });
