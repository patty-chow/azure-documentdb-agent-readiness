const mongoose = require('mongoose');
let connected = false;

async function connect(uri, options = {}) {
  if (connected) return mongoose;
  // Default options tuned for a demo long-running server; single process reuse.
  const defaults = {
    dbName: 'sample_fintech_20',
    // keep TLS; DOCUMENTDB_URI should include tls=true
    // follow readiness guidance: do not enable retryWrites by default
    retryWrites: false,
    // moderate pool for a demo app
    maxPoolSize: 10,
    // use new URL parser and unified topology by default (mongoose handles it)
  };
  const cfg = Object.assign({}, defaults, options);
  await mongoose.connect(uri, cfg);
  connected = true;
  return mongoose;
}

async function disconnect() {
  if (!connected) return;
  await mongoose.disconnect();
  connected = false;
}

module.exports = { connect, disconnect, mongoose };