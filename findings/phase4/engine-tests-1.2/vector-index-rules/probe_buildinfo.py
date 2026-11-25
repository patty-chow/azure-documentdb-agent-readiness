#!/usr/bin/env python
"""Print buildInfo and hello from documentdb-local without printing credentials."""
import json, os, re
import pymongo
from bson.json_util import dumps, RELAXED_JSON_OPTIONS

ENV = '/private/tmp/claude-501/-Users-julietai-claude/40f65f7c-640c-44c6-8eab-a8434709e1ff/scratchpad/engine-tests/local.env'

def load_env(path):
    env = {}
    for line in open(path):
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        line = re.sub(r'^export\s+', '', line)
        k, _, v = line.partition('=')
        env[k] = v.strip().strip('"').strip("'")
    return env

env = load_env(ENV)
c = pymongo.MongoClient(env['LOCAL_URI'], tlsAllowInvalidCertificates=True, serverSelectionTimeoutMS=15000)
for cmd in ('buildInfo', 'hello'):
    r = c.admin.command(cmd)
    print(cmd, dumps(r, json_options=RELAXED_JSON_OPTIONS))
