#!/bin/bash
# Reruns the driver-floors test. Throwaway venvs live under $WORK/venvs; outputs under $WORK/out.
set -u
WORK=/private/tmp/claude-501/-Users-julietai-claude/40f65f7c-640c-44c6-8eab-a8434709e1ff/scratchpad/engine-tests/driver-floors
ENVF=/private/tmp/claude-501/-Users-julietai-claude/40f65f7c-640c-44c6-8eab-a8434709e1ff/scratchpad/engine-tests/local.env
set -a; . "$ENVF"; set +a
mkdir -p "$WORK/venvs" "$WORK/out" "$WORK/sdists"
export PIP_DISABLE_PIP_VERSION_CHECK=1
python3 --version > "$WORK/out/python_version.txt" 2>&1
which python3 >> "$WORK/out/python_version.txt"

mk() { # mk <name> <pip spec...>
  local name=$1; shift
  local v="$WORK/venvs/$name"
  rm -rf "$v"; python3 -m venv "$v"
  "$v/bin/pip" install -q "$@" > "$WORK/out/$name.install.log" 2>&1; echo "exit=$?" >> "$WORK/out/$name.install.log"
  "$v/bin/pip" freeze > "$WORK/out/$name.freeze.txt" 2>&1
}

for ver in 4.8.0 4.9.0 4.11.0 4.13.0; do
  mk "pymongo-$ver" "pymongo==$ver"
  "$WORK/venvs/pymongo-$ver/bin/python" -I "$WORK/probe.py" > "$WORK/out/pymongo-$ver.probe.json" 2> "$WORK/out/pymongo-$ver.probe.err"
done

mk beanie2 "beanie>=2,<3"
"$WORK/venvs/beanie2/bin/python" -I "$WORK/beanie_probe.py" > "$WORK/out/beanie2.probe.json" 2> "$WORK/out/beanie2.probe.err"
mk beanie1 "beanie<2"
"$WORK/venvs/beanie1/bin/python" -I "$WORK/beanie_probe.py" > "$WORK/out/beanie1.probe.json" 2> "$WORK/out/beanie1.probe.err"

# changelog check: pymongo 4.6.3 vs 4.7.0 sdists
: > "$WORK/out/sdist_download.log"
for sv in 4.6.3 4.7.0; do "$WORK/venvs/pymongo-4.13.0/bin/pip" download --no-deps --no-binary :all: "pymongo==$sv" -d "$WORK/sdists" >> "$WORK/out/sdist_download.log" 2>&1; echo "exit=$? for pymongo==$sv" >> "$WORK/out/sdist_download.log"; done
for t in "$WORK"/sdists/pymongo-*.tar.gz; do tar -xzf "$t" -C "$WORK/sdists"; done
for d in "$WORK"/sdists/pymongo-4.6.3 "$WORK"/sdists/pymongo-4.7.0; do
  b=$(basename "$d"); f="$d/doc/changelog.rst"
  { echo "file=$f"; ls -la "$f" 2>&1; echo "--- grep -n -i OIDC (count then lines) ---"; grep -c -i "OIDC" "$f"; grep -n -i "OIDC" "$f" | head -40; } > "$WORK/out/$b.changelog_oidc.txt" 2>&1
done
# first changelog heading mentioning OIDC in 4.7.0 changelog
for sv in 4.6.3 4.7.0; do awk '/^Changes in Version/{h=$0} /OIDC|oidc/{print h" :: "$0}' "$WORK/sdists/pymongo-$sv/doc/changelog.rst" > "$WORK/out/pymongo-$sv.changelog_oidc_by_section.txt" 2>&1; done

# Node driver
npm view [email redacted] time --json > "$WORK/out/npm_mongodb_6.6.0_time.json" 2>&1
npm view [email redacted] time --json > "$WORK/out/npm_mongodb_6.7.0_time.json" 2>&1
python3 -c "import json;t=json.load(open(\"$WORK/out/npm_mongodb_6.6.0_time.json\"));print(t.get(\"6.6.0\"))" > "$WORK/out/npm_mongodb_6.6.0_time_key.txt" 2>&1
python3 -c "import json;t=json.load(open(\"$WORK/out/npm_mongodb_6.7.0_time.json\"));print(t.get(\"6.7.0\"))" > "$WORK/out/npm_mongodb_6.7.0_time_key.txt" 2>&1
npm view [email redacted] version dist.tarball peerDependencies --json > "$WORK/out/npm_mongodb_6.6.0_meta.json" 2>&1
npm view [email redacted] version dist.tarball peerDependencies --json > "$WORK/out/npm_mongodb_6.7.0_meta.json" 2>&1
curl -sS -L --max-time 60 -o "$WORK/out/node_release_6.7.0.json" -w '%{http_code}\n' "https://api.github.com/repos/mongodb/node-mongodb-native/releases/tags/v6.7.0" > "$WORK/out/node_release_6.7.0.http" 2>&1
curl -sS -L --max-time 60 -o "$WORK/out/node_release_6.6.0.json" -w '%{http_code}\n' "https://api.github.com/repos/mongodb/node-mongodb-native/releases/tags/v6.6.0" > "$WORK/out/node_release_6.6.0.http" 2>&1
/Users/julietai/claude/azure-documentdb-agent-readiness/.venv/bin/python -c "
import pymongo, json, os
c=pymongo.MongoClient(os.environ['LOCAL_URI'], serverSelectionTimeoutMS=5000)
bi=c.admin.command('buildInfo'); h=c.admin.command('hello')
json.dump({'version':bi.get('version'),'versionArray':bi.get('versionArray'),'maxBsonObjectSize':bi.get('maxBsonObjectSize'),'hello.maxWireVersion':h.get('maxWireVersion'),'hello.saslSupportedMechs':h.get('saslSupportedMechs'),'full_buildInfo_keys':sorted(bi.keys())}, open('$WORK/out/buildinfo.json','w'), default=str)"
python3 -I "$WORK/build_report.py"
echo done
