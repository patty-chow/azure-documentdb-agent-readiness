require('dotenv').config();
const { fetchHeadlines } = require('./scraper');
const { analyzeHeadlineLLM, embedText } = require('./ai');
const { getDb, getClient } = require('./db');
const fetch = globalThis.fetch || require('node-fetch');

async function notify(match, article){
  const webhook = process.env.WEBHOOK_URL;
  const payload = { type: 'alert', match, article };
  console.log('ALERT:', JSON.stringify(payload, null, 2));
  if(webhook){
    try{
      await fetch(webhook, { method: 'POST', headers: {'content-type':'application/json'}, body: JSON.stringify(payload) });
      console.log('Posted webhook to', webhook);
    }catch(e){
      console.warn('Webhook post failed', e.message||e);
    }
  }
}

async function run(){
  const items = await fetchHeadlines();
  const db = await getDb();
  const articles = db.collection('articles');
  const watchlist = db.collection('watchlist');

  for(const it of items){
    const headline = it.headline;
    const analysis = await analyzeHeadlineLLM(headline);
    const embedding = await embedText(headline);
    const doc = {
      headline,
      sentiment: analysis.sentiment || 0,
      tickers: analysis.tickers || [],
      timestamp: new Date(),
    };
    if(embedding) doc.embedding = embedding;
    // insert doc
    const res = await articles.insertOne(doc);
    console.log('Stored article', res.insertedId.toString(), 'sentiment', doc.sentiment, 'tickers', doc.tickers);

    // Alert agent: check watchlist for any matching tickers
    if((doc.tickers||[]).length>0){
      const matches = await watchlist.find({ ticker: { $in: doc.tickers } }).toArray();
      if(matches.length>0){
        for(const m of matches){
          await notify(m, doc);
        }
      }
    }
  }
}

if(require.main === module){
  run().then(()=>{ console.log('Run complete'); process.exit(0); }).catch(err=>{ console.error(err); process.exit(1); });
}

module.exports = { run };
