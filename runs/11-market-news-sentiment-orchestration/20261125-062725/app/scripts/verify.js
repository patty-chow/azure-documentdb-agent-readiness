// Quick DB verification: count articles, show indexes, show one sample article
require('dotenv').config();
const { MongoClient } = require('mongodb');
const SAMPLE_DB = 'sample_fintech_11';

async function main(){
  const uri = process.env.DOCUMENTDB_URI;
  if(!uri){ console.error('DOCUMENTDB_URI not set'); process.exit(2); }
  const client = new MongoClient(uri);
  await client.connect();
  const db = client.db(SAMPLE_DB);
  const articles = db.collection('articles');
  const count = await articles.countDocuments();
  console.log('articles.count=', count);
  const idx = await articles.indexes();
  console.log('indexes=', idx);
  const one = await articles.findOne({}, { projection: { headline:1, sentiment:1, tickers:1, embedding:1 } });
  console.log('one article=', one);
  await client.close();
}
main().then(()=>process.exit(0)).catch(e=>{ console.error(e); process.exit(1); });
