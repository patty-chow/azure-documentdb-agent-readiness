const Parser = require('rss-parser');
const parser = new Parser();

// simple RSS scraper that returns a few recent headlines
async function scrapeReutersBusiness(limit = 5) {
  // Reuters business RSS
  const feedUrl = 'https://feeds.reuters.com/reuters/businessNews';
  const feed = await parser.parseURL(feedUrl);
  const items = feed.items.slice(0, limit).map(i => ({
    headline: i.title,
    link: i.link,
    source: 'reuters',
    timestamp: i.pubDate ? new Date(i.pubDate) : new Date()
  }));
  return items;
}

module.exports = { scrapeReutersBusiness };
