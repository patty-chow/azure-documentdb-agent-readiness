#!/bin/sh
# Companion to run.py: pull the gateway/postgres log lines for database t_txn from the documentdb-local container
# (read-only; strips ANSI colour, duplicate GATEWAY-FILE echo lines and anything that could carry credentials).
docker logs --since "${1:-15m}" --timestamps ddb-engine-test 2>&1 | sed -E 's/\x1b\[[0-9;]*m//g' | grep -v "GATEWAY-FILE" \
 | grep -v -i -E "password|secret|cron job|stream_driver|accept a TCP|role \"postgres\"|role \"root\"" \
 | grep -E "t_txn|abandoned|drop a transaction|Connection error|Lock not available|idle-in-transaction" \
 | sed -E 's/network.connection.id=[^ ]+ //; s/request.id=[0-9]+ //; s/span.kind="[a-z]+" //g; s/db.system.name="[a-z]+" //g; s/network.protocol.name=TCP //; s/tls.established=true //; s/gateway.request\{[^}]*\}:gateway.process_request\{[^}]*\}://; s/postgres.execute\{[^}]*\}://' \
 | cut -c1-400
