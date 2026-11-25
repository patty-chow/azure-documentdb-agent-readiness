require('dotenv').config();
const express = require('express');
const axios = require('axios');
const { connect, disconnect } = require('./mongo');
const { createCache } = require('./cache');

async function main() {
  const uri = process.env.DOCUMENTDB_URI;
  if (!uri) {
    console.error('DOCUMENTDB_URI not set - copy .env.example to .env and set it');
    process.exit(1);
  }

  await connect(uri);
  console.log('Connected to DocumentDB (sample_fintech_20).');

  // demo-friendly TTLs per earlier decision
  const ttlSeconds = 5; // demo: 5s TTL
  const staleWindowSeconds = 10; // demo: allow 10s stale-while-revalidate

  // fetcher function using axios to talk to an upstream HTTP echo service
  async function fetcher(options) {
    const { method, url, params, data } = options;
    const res = await axios({ method, url, params, data, timeout: 10000 });
    return { data: res.data, status: res.status, headers: res.headers };
  }

  const cache = createCache({ ttlSeconds, staleWindowSeconds, fetcher });

  const app = express();
  app.use(express.json());

  // route: /proxy forwards to https://httpbin.org/get and demonstrates caching
  app.get('/proxy', cache.expressMiddleware({ urlBuilder: (req) => 'https://httpbin.org/get' }));

  const server = app.listen(0, async () => {
    const port = server.address().port;
    console.log(`Demo server listening on http://localhost:${port}`);

    const client = axios.create({ baseURL: `http://localhost:${port}`, timeout: 10000 });

    try {
      console.log('\n1) First request -> expected network fetch (miss)');
      let r1 = await client.get('/proxy', { params: { q: 'first' } });
      console.log('Response source:', r1.data.origin ? 'network (httpbin)' : 'cache');

      console.log('\n2) Immediate second request -> expected cache hit (fresh)');
      let r2 = await client.get('/proxy', { params: { q: 'first' } });
      console.log('Served quickly, likely from cache, response snippet:', JSON.stringify(r2.data.args || r2.data).slice(0,120));

      console.log(`\nWaiting ${ttlSeconds + 1}s for TTL to expire (but remain within stale window)...`);
      await new Promise(r => setTimeout(r, (ttlSeconds + 1) * 1000));

      console.log('\n3) After TTL expiry but within stale window -> expect stale served immediately and background refresh');
      let r3 = await client.get('/proxy', { params: { q: 'first' } });
      console.log('Response (stale or refreshed):', JSON.stringify(r3.data).slice(0,120));

      console.log(`\nWaiting ${staleWindowSeconds + 1}s for stale window to lapse so next request forces synchronous refresh...`);
      await new Promise(r => setTimeout(r, (staleWindowSeconds + 1) * 1000));

      console.log('\n4) After stale window -> expect synchronous network fetch');
      let r4 = await client.get('/proxy', { params: { q: 'first' } });
      console.log('Final response snippet:', JSON.stringify(r4.data).slice(0,120));

      console.log('\nDemo finished. Shutting down.');
    } catch (err) {
      console.error('Demo encountered error:', err.message);
    } finally {
      server.close(async () => {
        await disconnect();
        process.exit(0);
      });
    }
  });
}

main().catch(err => { console.error(err); process.exit(1); });
