const { scrapeReutersBusiness } = require('./scraper');
const { analyzeHeadline, notifyWebhook } = require('./agents');
const { getDb, ensureIndexes, client } = require('./db');

async function runDemo() {
  console.log('Starting demo pipeline...');
  await ensureIndexes();
  let headlines = [];
  try {
    headlines = await scrapeReutersBusiness(5);
    console.log('Scraped', headlines.length, 'headlines');
  } catch (e) {
    console.warn('Scrape failed; falling back to local sample headlines:', e.message);
    headlines = [
      { headline: 'AAPL shares rise after strong iPhone sales', link: '', source: 'sample', timestamp: new Date() },
      { headline: 'Oil prices fall as demand outlook weakens', link: '', source: 'sample', timestamp: new Date() },
      { headline: 'TSLA plunges after delivery miss', link: '', source: 'sample', timestamp: new Date() }
    ];
  }

  const db = await getDb();
  const signals = db.collection('sentiment_signals');
  const watchlist = db.collection('watchlist');

  // ensure watchlist has an example entry (idempotent seed)
  try {
    await watchlist.updateOne({ ticker: 'AAPL' }, { $setOnInsert: { ticker: 'AAPL', note: 'Seed watchlist for demo' } }, { upsert: true });
  } catch (e) {
    console.warn('Watchlist seed failed', e.message);
  }

  for (const item of headlines) {
    console.log('\nProcessing:', item.headline);
    const analysis = await analyzeHeadline(item.headline);
    console.log('Analysis:', analysis);
    const doc = {
      headline: item.headline,
      link: item.link,
      source: item.source,
      timestamp: item.timestamp || new Date(),
      sentiment_score: analysis.sentiment_score,
      tickers: analysis.tickers,
      metadata: {}
    };
    const r = await signals.insertOne(doc);
    console.log('Inserted document id', r.insertedId);

    // check watchlist matches
    if (analysis.tickers && analysis.tickers.length) {
      const matches = await watchlist.find({ ticker: { $in: analysis.tickers } }).toArray();
      if (matches.length) {
        console.log('Watchlist match for tickers:', matches.map(m => m.ticker));
        // send notification
        await notifyWebhook({ type: 'watchlist_alert', tickers: analysis.tickers, headline: item.headline, sentiment: analysis.sentiment_score, docId: r.insertedId.toString() });
      } else {
        console.log('No watchlist matches');
      }
    }
  }

  await client.close();
  console.log('Demo finished');
}

if (require.main === module) {
  runDemo().catch(e => {
    console.error('Demo failed', e);
    process.exit(1);
  });
}
