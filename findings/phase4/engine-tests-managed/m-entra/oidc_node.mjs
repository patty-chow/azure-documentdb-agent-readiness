// MONGODB-OIDC against Azure DocumentDB with the Node.js driver (6.6.0, 6.7.0, latest).
// Usage: node oidc_node.mjs <node_dir_with_node_modules> <unmasked_out_json>
// Env: M_PLAIN_HOST, M_GLOBAL_HOST. Never prints or stores the access token.
import { createRequire } from 'node:module';
import fs from 'node:fs';

const NODE_DIR = process.argv[2];
const OUT = process.argv[3];
const PLAIN = process.env.M_PLAIN_HOST;
const GLOBAL = process.env.M_GLOBAL_HOST;
const require = createRequire(NODE_DIR + '/package.json');
const { AzureCliCredential } = require('@azure/identity');
const SCOPE = 'https://ossrdbms-aad.database.windows.net/.default';
const credential = new AzureCliCredential();

const results = {
  node: process.version,
  azure_identity: require('@azure/identity/package.json').version,
  started_at: new Date().toISOString(),
  runs: [],
};

function errInfo(e, depth = 0) {
  if (!e) return null;
  const d = { name: e.name, constructor: e.constructor && e.constructor.name, message: e.message };
  for (const k of ['code', 'codeName', 'errmsg']) if (e[k] !== undefined) d[k] = e[k];
  try { if (e.errorLabels && e.errorLabels.length !== undefined) d.errorLabels = Array.from(e.errorLabels); } catch { /* ignore */ }
  if (e.errorResponse) d.errorResponse = e.errorResponse;
  if (e.cause && depth < 3) d.cause = errInfo(e.cause, depth + 1);
  if (e.reason && depth < 3) {
    try {
      const servers = e.reason.servers ? Array.from(e.reason.servers.values()).map((s) => ({ address: s.address, type: s.type, error: s.error ? errInfo(s.error, depth + 1) : null })) : undefined;
      d.reason = { type: e.reason.type, servers };
    } catch { d.reason = String(e.reason); }
  }
  return d;
}

function oidcCallback(calls, expiry) {
  // Learn's shape: OIDC_CALLBACK returning { accessToken, expiresInSeconds }.
  return async (params) => {
    const c = {
      at: new Date().toISOString(),
      paramKeys: Object.keys(params || {}),
      version: params && params.version,
      username: params && params.username !== undefined ? params.username : null,
      idpInfo: params && params.idpInfo ? params.idpInfo : null,
      hasRefreshToken: !!(params && params.refreshToken),
    };
    calls.push(c);
    const t = await credential.getToken(SCOPE);
    const expiresInSeconds = expiry === 'learn-ts'
      ? ((t && t.expiresOnTimestamp) || 0) - Math.floor(Date.now() / 1000) // Learn's TypeScript sample, verbatim
      : Math.floor((t.expiresOnTimestamp - Date.now()) / 1000);
    c.expiresInSeconds = expiresInSeconds;
    return { accessToken: (t && t.token) || '', expiresInSeconds };
  };
}

function legacyRequestTokenCallback(calls) {
  // Pre-GA 6.6.0 shape: REQUEST_TOKEN_CALLBACK(info, context) -> { accessToken, expiresInSeconds }
  return async (info, context) => {
    calls.push({ at: new Date().toISOString(), info: info || null, context: context || null });
    const t = await credential.getToken(SCOPE);
    return { accessToken: t.token, expiresInSeconds: Math.floor((t.expiresOnTimestamp - Date.now()) / 1000) };
  };
}

async function runCase({ label, mod, host, makeProps, propsDisplay }) {
  const { MongoClient } = require(mod);
  const calls = [];
  const hostVal = host === 'global' ? GLOBAL : PLAIN;
  const rec = {
    label,
    driver_package: mod,
    driver_version: require(mod + '/package.json').version,
    host_form: host,
    call: `new MongoClient('mongodb+srv://${hostVal}/', { connectTimeoutMS: 120000, serverSelectionTimeoutMS: 20000, tls: true, retryWrites: false, maxIdleTimeMS: 120000, authMechanism: 'MONGODB-OIDC', authMechanismProperties: ${propsDisplay} }); await client.connect(); await client.db('admin').command({ ping: 1 }); await client.db('mt_entra').collection('items').find({}, { projection: { _id: 0 } }).sort({ n: 1 }).toArray()`,
    steps: [],
    callback_calls: calls,
  };
  let client;
  try {
    client = new MongoClient(`mongodb+srv://${hostVal}/`, {
      connectTimeoutMS: 120000,
      serverSelectionTimeoutMS: 20000,
      tls: true,
      retryWrites: false,
      maxIdleTimeMS: 120000,
      appName: `m-entra-node-${label}`,
      authMechanism: 'MONGODB-OIDC',
      authMechanismProperties: makeProps(calls),
    });
    rec.steps.push({ step: 'construct', ok: true });
  } catch (e) {
    rec.steps.push({ step: 'construct', ok: false, error: errInfo(e) });
    results.runs.push(rec);
    return;
  }
  const ops = [
    ['connect', async () => { await client.connect(); return 'connected'; }],
    ['ping', async () => client.db('admin').command({ ping: 1 })],
    ['find', async () => client.db('mt_entra').collection('items').find({}, { projection: { _id: 0 } }).sort({ n: 1 }).toArray()],
  ];
  for (const [name, fn] of ops) {
    const t0 = Date.now();
    try {
      const r = await fn();
      rec.steps.push({ step: name, ok: true, result: r, ms: Date.now() - t0 });
    } catch (e) {
      rec.steps.push({ step: name, ok: false, error: errInfo(e), ms: Date.now() - t0 });
    }
  }
  try { await client.close(); } catch { /* ignore */ }
  results.runs.push(rec);
}

const AZ = ['*.azure.com'];
const MC = ['*.mongocluster.cosmos.azure.com'];
const cases = [];
for (const [ver, mod] of [['6.6.0', 'mongodb660'], ['6.7.0', 'mongodb670'], ['latest', 'mongodblatest']]) {
  cases.push({ label: `${ver}-oidc_callback-allowed-azure.com`, mod, host: 'plain',
    makeProps: (calls) => ({ OIDC_CALLBACK: oidcCallback(calls), ALLOWED_HOSTS: AZ }),
    propsDisplay: "{ OIDC_CALLBACK: <callback returning AzureCliCredential token>, ALLOWED_HOSTS: ['*.azure.com'] }" });
  cases.push({ label: `${ver}-oidc_callback-allowed-mongocluster`, mod, host: 'plain',
    makeProps: (calls) => ({ OIDC_CALLBACK: oidcCallback(calls), ALLOWED_HOSTS: MC }),
    propsDisplay: "{ OIDC_CALLBACK: <callback returning AzureCliCredential token>, ALLOWED_HOSTS: ['*.mongocluster.cosmos.azure.com'] }" });
  cases.push({ label: `${ver}-oidc_callback-no-allowed-hosts`, mod, host: 'plain',
    makeProps: (calls) => ({ OIDC_CALLBACK: oidcCallback(calls) }),
    propsDisplay: '{ OIDC_CALLBACK: <callback returning AzureCliCredential token> }' });
  if (ver !== '6.6.0') {
    cases.push({ label: `${ver}-learn-ts-expiry-allowed-azure.com`, mod, host: 'plain',
      makeProps: (calls) => ({ OIDC_CALLBACK: oidcCallback(calls, 'learn-ts'), ALLOWED_HOSTS: AZ }),
      propsDisplay: "{ OIDC_CALLBACK: <Learn TypeScript callback: expiresInSeconds = expiresOnTimestamp - Math.floor(Date.now()/1000)>, ALLOWED_HOSTS: ['*.azure.com'] }" });
  } else {
    cases.push({ label: `${ver}-legacy-request_token_callback-allowed-mongocluster`, mod, host: 'plain',
      makeProps: (calls) => ({ REQUEST_TOKEN_CALLBACK: legacyRequestTokenCallback(calls), ALLOWED_HOSTS: MC }),
      propsDisplay: "{ REQUEST_TOKEN_CALLBACK: <pre-GA callback (info, context) returning AzureCliCredential token>, ALLOWED_HOSTS: ['*.mongocluster.cosmos.azure.com'] }" });
  }
}
cases.push({ label: 'latest-oidc_callback-allowed-mongocluster-global-host', mod: 'mongodblatest', host: 'global',
  makeProps: (calls) => ({ OIDC_CALLBACK: oidcCallback(calls), ALLOWED_HOSTS: MC }),
  propsDisplay: "{ OIDC_CALLBACK: <callback returning AzureCliCredential token>, ALLOWED_HOSTS: ['*.mongocluster.cosmos.azure.com'] }" });

for (const c of cases) {
  await runCase(c);
  const r = results.runs[results.runs.length - 1];
  console.log(JSON.stringify({ label: r.label, v: r.driver_version, steps: r.steps.map((s) => [s.step, s.ok ? 'ok' : `${s.error && s.error.name}: ${s.error && s.error.message}`.slice(0, 200)]), callbacks: r.callback_calls.length }));
}
results.finished_at = new Date().toISOString();
fs.writeFileSync(OUT, JSON.stringify(results, null, 1), { mode: 0o600 });
