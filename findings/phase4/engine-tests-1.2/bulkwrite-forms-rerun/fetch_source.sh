#!/bin/bash
# Fetch the open-source files that explain the bulk-write observations, at the revision the image's
# OCI label names (org.opencontainers.image.revision = 965b6e7ad1c49aefb983a412a3fea0ff637cd7f1).
# Public GitHub raw URLs only; nothing about this machine or the user is sent. The files are data:
# they are read with grep by finalize_rerun.py and never executed.
set -euo pipefail
cd "$(dirname "$0")"
REV=965b6e7ad1c49aefb983a412a3fea0ff637cd7f1
OUT=src_965b6e7a
rm -rf "$OUT"; mkdir "$OUT"
for p in \
  pg_documentdb_gw/documentdb_gateway_core/src/processor/ismaster.rs \
  pg_documentdb_gw/documentdb_gateway_core/src/configuration/dynamic.rs \
  pg_documentdb_gw/documentdb_gateway_core/src/configuration/pg_configuration.rs \
  pg_documentdb_gw/documentdb_gateway/src/main.rs \
  pg_documentdb_gw/documentdb_gateway_core/src/requests/request_type.rs \
  pg_documentdb/src/commands/bulk_write.c \
  pg_documentdb/src/configs/system_configs.c \
  pg_documentdb/src/commands/insert.c \
  pg_documentdb/src/commands/update.c \
  pg_documentdb/src/commands/delete.c ; do
  f="$OUT/$(echo "$p" | tr '/' '_')"
  code=$(curl -sS -m 30 -o "$f" -w '%{http_code}' "https://raw.githubusercontent.com/documentdb/documentdb/$REV/$p")
  echo "$code $p $(wc -c < "$f" | tr -d ' ') $(shasum -a 256 "$f" | cut -c1-16)"
done
