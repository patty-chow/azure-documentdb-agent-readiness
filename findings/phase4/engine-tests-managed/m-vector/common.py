"""Shared helpers for the m-vector managed-service test (database mt_vector only).

- Reads ../managed.env without ever printing it.
- Every recorded or printed string passes through scrub(), which removes the password,
  both URIs (raw, URL-encoded and JSON-escaped forms), e-mail addresses and GUIDs
  (subscription, tenant and object ids look like GUIDs).
- run() sends one raw database command and records the exact command and the exact raw
  server reply (or the raw error document: code, codeName, errmsg, errorLabels).
"""
import datetime
import json
import os
import re
import sys
import time
import urllib.parse
import warnings

import pymongo
from bson.json_util import dumps, RELAXED_JSON_OPTIONS
from pymongo.errors import OperationFailure, PyMongoError

HERE = os.path.dirname(os.path.abspath(__file__))
ENV_PATH = os.path.join(HERE, '..', 'managed.env')
DB_NAME = 'mt_vector'

warnings.filterwarnings('ignore', category=UserWarning, message=r'.*CosmosDB.*')


def _load_env(path):
    env = {}
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            line = re.sub(r'^export\s+', '', line)
            k, _, v = line.partition('=')
            env[k.strip()] = v.strip().strip('"').strip("'")
    return env


ENV = _load_env(ENV_PATH)

_secrets = set()
for key in ('MANAGED_PASS', 'MANAGED_URI', 'MANAGED_GLOBAL_URI'):
    val = ENV.get(key)
    if val:
        _secrets.update({val, urllib.parse.quote(val, safe=''), urllib.parse.quote_plus(val),
                         json.dumps(val)[1:-1]})
_SECRETS = sorted((s for s in _secrets if len(s) >= 6), key=len, reverse=True)
_GUID = re.compile(r'\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\b')
_EMAIL = re.compile(r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}')


def scrub(text):
    for s in _SECRETS:
        text = text.replace(s, '<redacted>')
    text = _EMAIL.sub('<email-masked>', text)
    text = _GUID.sub('<guid-masked>', text)
    return text


def j(obj):
    """BSON-aware JSON (relaxed extended JSON), scrubbed, returned as plain Python data."""
    return json.loads(scrub(dumps(obj, json_options=RELAXED_JSON_OPTIONS)))


def now_utc():
    return datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='milliseconds')


def get_client(**overrides):
    opts = dict(serverSelectionTimeoutMS=30000, connectTimeoutMS=20000,
                socketTimeoutMS=300000, appname='mt-vector-test')
    opts.update(overrides)
    return pymongo.MongoClient(ENV['MANAGED_URI'], **opts)


class Recorder:
    def __init__(self, out_name):
        self.path = os.path.join(HERE, out_name)
        self.steps = []

    def add(self, rec):
        self.steps.append(j(rec))
        self.save()

    def save(self):
        with open(self.path, 'w') as f:
            json.dump(self.steps, f, indent=2)

    def run(self, db, step, part, question, cmd, *, extra=False, oss_step=None, note=None, quiet=False):
        """Send one raw command with db.command(cmd); record exact command and raw reply/error."""
        rec = {'step': step, 'part': part, 'question': question, 'extra': extra,
               'driver_call': f'pymongo Database("{db.name}").command(<command>)',
               'command': cmd, 'at_utc': now_utc()}
        if oss_step:
            rec['oss_step'] = oss_step
        if note:
            rec['note'] = note
        t0 = time.time()
        try:
            resp = db.command(cmd)
            rec['outcome'] = 'ok'
            rec['response'] = resp
        except OperationFailure as e:
            det = e.details or {}
            rec['outcome'] = 'error'
            rec['error'] = {'code': e.code, 'codeName': det.get('codeName'),
                            'errmsg': det.get('errmsg', str(e)),
                            'errorLabels': det.get('errorLabels'),
                            'raw': det}
        except PyMongoError as e:
            rec['outcome'] = 'driver_error'
            rec['error'] = {'code': None, 'codeName': type(e).__name__, 'errmsg': str(e),
                            'errorLabels': None}
        rec['elapsed_s'] = round(time.time() - t0, 3)
        self.add(rec)
        out = self.steps[-1]
        if not quiet:
            body = out.get('response') if out['outcome'] == 'ok' else {k: v for k, v in out['error'].items() if k != 'raw'}
            text = json.dumps(body)
            print(f"[{step}] {out['outcome']} ({out['elapsed_s']}s): {text[:600]}", flush=True)
        return out

    def note(self, step, part, question, driver_call, response, reading=None, extra=False, oss_step=None):
        rec = {'step': step, 'part': part, 'question': question, 'extra': extra,
               'driver_call': driver_call, 'at_utc': now_utc(), 'outcome': 'ok', 'response': response}
        if oss_step:
            rec['oss_step'] = oss_step
        if reading:
            rec['reading'] = reading
        self.add(rec)
        print(f"[{step}] {json.dumps(self.steps[-1]['response'])[:600]}", flush=True)
        return self.steps[-1]


# ---------- command builders -------------------------------------------------

DOCS = [
    {'_id': 1, 'tag': 'a', 'v': [1.0, 0.0, 0.0]},
    {'_id': 2, 'tag': 'b', 'v': [0.0, 1.0, 0.0]},
    {'_id': 3, 'tag': 'c', 'v': [0.0, 0.0, 1.0]},
    {'_id': 4, 'tag': 'd', 'v': [0.9, 0.1, 0.0]},
    {'_id': 5, 'tag': 'e', 'v': [0.1, 0.9, 0.0]},
]


def ci(coll, indexes):
    return {'createIndexes': coll, 'indexes': indexes}


def hnsw(name, path='v', dims=3, **opts):
    o = {'kind': 'vector-hnsw', 'dimensions': dims, 'similarity': 'COS', 'm': 16, 'efConstruction': 64}
    o.update(opts)
    return {'name': name, 'key': {path: 'cosmosSearch'}, 'cosmosSearchOptions': o}


def ivf(name, path='v', dims=3, numLists=1, **opts):
    o = {'kind': 'vector-ivf', 'dimensions': dims, 'similarity': 'COS', 'numLists': numLists}
    o.update(opts)
    return {'name': name, 'key': {path: 'cosmosSearch'}, 'cosmosSearchOptions': o}


def diskann(name, path='v', dims=3, **opts):
    o = {'kind': 'vector-diskann', 'dimensions': dims, 'similarity': 'COS', 'maxDegree': 32, 'lBuild': 50}
    o.update(opts)
    return {'name': name, 'key': {path: 'cosmosSearch'}, 'cosmosSearchOptions': o}


def search(coll, vector, path='v', k=3, extra=None):
    cs = {'vector': vector, 'path': path, 'k': k}
    if extra:
        cs.update(extra)
    return {'aggregate': coll, 'pipeline': [
        {'$search': {'cosmosSearch': cs, 'returnStoredSource': True}},
        {'$project': {'_id': 1, 'tag': 1, 'v': 1, 'score': {'$meta': 'searchScore'}}},
    ], 'cursor': {}}


def ids_of(rec):
    if rec.get('outcome') != 'ok':
        return None
    return [d.get('_id') for d in rec['response']['cursor']['firstBatch']]
