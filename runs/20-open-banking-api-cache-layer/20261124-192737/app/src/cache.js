const crypto = require('crypto');
const ApiCache = require('./models/ApiCache');

function computeKey(options) {
  // options: { method, url, params, body }
  // Normalize method + url + sorted params + body JSON
  const method = (options.method || 'GET').toUpperCase();
  const url = options.url;
  const params = options.params ? JSON.stringify(sortObject(options.params)) : '';
  const body = options.data ? JSON.stringify(options.data) : '';
  const raw = `${method} ${url} ${params} ${body}`;
  return crypto.createHash('sha256').update(raw).digest('hex');
}

function sortObject(obj) {
  if (!obj || typeof obj !== 'object' || Array.isArray(obj)) return obj;
  const out = {};
  Object.keys(obj).sort().forEach(k => {
    out[k] = sortObject(obj[k]);
  });
  return out;
}

function createCache({ ttlSeconds = 60, staleWindowSeconds = 300, fetcher }) {
  if (typeof fetcher !== 'function') throw new Error('fetcher must be provided');

  async function getOrUpdate(options) {
    const key = computeKey(options);
    const now = new Date();
    const doc = await ApiCache.findOne({ key }).lean();

    if (!doc) {
      // miss: fetch synchronously
      const res = await fetcher(options);
      const expiresAt = new Date(Date.now() + ttlSeconds * 1000);
      const staleUntil = new Date(Date.now() + (ttlSeconds + staleWindowSeconds) * 1000);
      await ApiCache.updateOne({ key }, {
        $set: {
          response: res.data,
          statusCode: res.status,
          headers: res.headers,
          cachedAt: now,
          expiresAt,
          staleUntil
        }
      }, { upsert: true });
      return { source: 'network', ...res };
    }

    const nowTs = Date.now();
    if (nowTs < new Date(doc.expiresAt).getTime()) {
      // fresh
      return { source: 'cache', data: doc.response, status: doc.statusCode, headers: doc.headers };
    }

    // expired
    if (nowTs < new Date(doc.staleUntil).getTime()) {
      // stale-while-revalidate: return stale immediately and refresh in background
      backgroundRefresh(key, options);
      return { source: 'stale-cache', data: doc.response, status: doc.statusCode, headers: doc.headers };
    }

    // stale beyond staleUntil: fetch synchronously
    const res2 = await fetcher(options);
    const expiresAt2 = new Date(Date.now() + ttlSeconds * 1000);
    const staleUntil2 = new Date(Date.now() + (ttlSeconds + staleWindowSeconds) * 1000);
    await ApiCache.updateOne({ key }, {
      $set: {
        response: res2.data,
        statusCode: res2.status,
        headers: res2.headers,
        cachedAt: new Date(),
        expiresAt: expiresAt2,
        staleUntil: staleUntil2
      }
    }, { upsert: true });
    return { source: 'network', ...res2 };
  }

  // ensure only one background refresh per key at a time
  const inFlight = new Map();
  async function backgroundRefresh(key, options) {
    if (inFlight.has(key)) return;
    inFlight.set(key, true);
    (async () => {
      try {
        const res = await fetcher(options);
        const expiresAt = new Date(Date.now() + ttlSeconds * 1000);
        const staleUntil = new Date(Date.now() + (ttlSeconds + staleWindowSeconds) * 1000);
        await ApiCache.updateOne({ key }, {
          $set: {
            response: res.data,
            statusCode: res.status,
            headers: res.headers,
            cachedAt: new Date(),
            expiresAt,
            staleUntil
          }
        }, { upsert: true });
      } catch (err) {
        // swallow: background refresh failures should not affect serving
        console.warn('background refresh failed', err && err.message ? err.message : err);
      } finally {
        inFlight.delete(key);
      }
    })();
  }

  // Express middleware adapter: assumes upstream URL is in req.query.target or a fixed backend
  function expressMiddleware({ urlBuilder }) {
    if (typeof urlBuilder !== 'function') throw new Error('urlBuilder func required');
    return async (req, res, next) => {
      try {
        const url = urlBuilder(req);
        const options = { method: req.method, url, params: req.query, data: req.body };
        const result = await getOrUpdate(options);
        res.set(result.headers || {});
        res.status(result.status || 200).json(result.data);
      } catch (err) {
        next(err);
      }
    };
  }

  return { getOrUpdate, expressMiddleware };
}

module.exports = { createCache, computeKey };
