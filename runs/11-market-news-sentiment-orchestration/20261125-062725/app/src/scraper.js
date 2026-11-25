// Simple scraper abstraction: if NEWS_API_KEY present it will try to fetch headlines from newsapi.org
// Otherwise returns a bundled sample of headlines.

const fetch = globalThis.fetch || require('node-fetch');

const SAMPLE_HEADLINES = [
  'AAPL reports record iPhone sales, shares jump',
  'TSLA plans new factory in Texas, supply chain updates',
  'Federal Reserve holds rates steady amid inflation concerns',
  'MSFT announces new AI features for Office suite',
  'AMZN Q4 earnings beat expectations, cloud grows',
  'Small-cap biotech hits milestone in cancer trial',
  'Energy stocks rally as oil prices climb',
  'Retail sector struggles despite holiday season',
  'Cryptocurrency volatility returns as Bitcoin tumbles',
  'Major bank fined for compliance lapses',
  'Auto suppliers face chip shortage delays',
  'Healthcare insurers revise premiums for next year',
  'Airline announces new transatlantic routes',
  'Fintech startup raises Series B led by major VC',
  'Oil giant outlines ambitious emissions plan',
  'Retailer files for bankruptcy protection',
  'Electric truck maker unveils prototype',
  'Semiconductor demand boosts manufacturing investments',
  'Pharma company receives patent for new drug',
  'Consumer confidence index rebounds'
];

async function fetchHeadlines(){
  const key = process.env.NEWS_API_KEY;
  if(!key){
    return SAMPLE_HEADLINES.map(h=>({headline:h}));
  }
  try{
    const url = `https://newsapi.org/v2/top-headlines?category=business&pageSize=20&apiKey=${key}`;
    const res = await fetch(url);
    const data = await res.json();
    if(data && data.articles){
      return data.articles.map(a=>({headline: a.title || a.description || ''})).filter(x=>x.headline);
    }
    return SAMPLE_HEADLINES.map(h=>({headline:h}));
  }catch(e){
    console.warn('News fetch failed, falling back to sample headlines', e.message||e);
    return SAMPLE_HEADLINES.map(h=>({headline:h}));
  }
}

module.exports = { fetchHeadlines };
