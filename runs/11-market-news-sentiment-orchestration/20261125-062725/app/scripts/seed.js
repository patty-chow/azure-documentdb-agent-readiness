/* Seed script: creates database sample_fintech_11 and inserts a small watchlist.
   Idempotent: uses upsert by ticker. */
require('dotenv').config();
const { MongoClient } = require('mongodb');
const SAMPLE_DB = 'sample_fintech_11';

const WATCHLIST = [
  { ticker: 'AAPL', alert: true },
  { ticker: 'TSLA', alert: true },
  { ticker: 'MSFT', alert: false },
  { ticker: 'AMZN', alert: true }
];

async function main(){
  const uri = process.env.DOCUMENTDB_URI;
  if(!uri){
    console.error('DOCUMENTDB_URI not set. See .env.example');
    process.exit(2);
  }
  const client = new MongoClient(uri);
  await client.connect();
  const db = client.db(SAMPLE_DB);
  const wl = db.collection('watchlist');
  for(const w of WATCHLIST){
    await wl.updateOne({ticker:w.ticker}, {$set:w}, {upsert:true});
    console.log('Upserted watchlist', w.ticker);
  }
  // Create indexes: text on headline and index on tickers
  const articles = db.collection('articles');
  try{
    await articles.createIndex({ headline: 'text' });
    await articles.createIndex({ tickers: 1 });
    console.log('Ensured indexes on articles');
  }catch(e){
    console.warn('Index creation may have failed:', e.message || e);
  }
  await client.close();
}

main().catch(err=>{console.error(err); process.exit(1)});
