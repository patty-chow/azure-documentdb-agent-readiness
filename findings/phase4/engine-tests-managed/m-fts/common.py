"""Shared helpers for the m-fts managed-service test (database mt_fts only).

- Reads ../managed.env without ever printing it.
- Every recorded or printed string passes through scrub(), which removes the password,
  both URIs (raw, URL-encoded and JSON-escaped forms) and the subscription id, and masks
  e-mail addresses and GUIDs (subscription, tenant and object ids look like GUIDs).
- Recorder.run() sends one raw database command and records the exact command and the exact
  raw server reply (or the raw error document: code, codeName, errmsg, errorLabels).
- az_bash() runs one Azure CLI command through `bash -c` with the exact command text (as on
  Learn, using $URL / $RESOURCE_ID variables) and returns rc, stdout (parsed when JSON) and stderr.
- ClusterMonitor samples the Learn "check" GET and `az documentdb mongocluster show` every N s.
"""
import datetime
import json
import os
import re
import subprocess
import threading
import time
import urllib.parse
import warnings

import pymongo
from bson.json_util import dumps, RELAXED_JSON_OPTIONS
from pymongo.errors import OperationFailure, PyMongoError

HERE = os.path.dirname(os.path.abspath(__file__))
ENV_PATH = os.path.join(HERE, '..', 'managed.env')
DB_NAME = 'mt_fts'
COLL = 'products'
API_VERSION = '2024-07-01'

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
RG = ENV['MANAGED_RG']
CLUSTER = ENV['MANAGED_CLUSTER']

_secret_lock = threading.Lock()
_secrets = set()
_named = {}   # exact value -> placeholder


def _register_secret(val, placeholder='<redacted>'):
    with _secret_lock:
        if val and len(val) >= 6:
            for form in {val, urllib.parse.quote(val, safe=''), urllib.parse.quote_plus(val),
                         json.dumps(val)[1:-1]}:
                _named[form] = placeholder


for _key in ('MANAGED_PASS', 'MANAGED_URI', 'MANAGED_GLOBAL_URI'):
    _register_secret(ENV.get(_key))

_GUID = re.compile(r'\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\b')
_EMAIL = re.compile(r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}')


def scrub(text):
    with _secret_lock:
        items = sorted(_named.items(), key=lambda kv: len(kv[0]), reverse=True)
    for s, ph in items:
        text = text.replace(s, ph)
    text = _EMAIL.sub('<email-masked>', text)
    text = _GUID.sub('<guid-masked>', text)
    return text


def j(obj):
    """BSON-aware JSON (relaxed extended JSON), scrubbed, returned as plain Python data."""
    return json.loads(scrub(dumps(obj, json_options=RELAXED_JSON_OPTIONS)))


def now_utc():
    return datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='milliseconds')


def iso(ts):
    return datetime.datetime.fromtimestamp(ts, datetime.timezone.utc).isoformat(timespec='milliseconds')


def get_client(**overrides):
    opts = dict(serverSelectionTimeoutMS=30000, connectTimeoutMS=20000,
                socketTimeoutMS=300000, appname='mt-fts-test')
    opts.update(overrides)
    return pymongo.MongoClient(ENV['MANAGED_URI'], **opts)


# ---------- Azure resource helpers -------------------------------------------------

_SUB = None


def subscription_id():
    global _SUB
    if _SUB is None:
        r = subprocess.run(['az', 'account', 'show', '--query', 'id', '-o', 'tsv'],
                           capture_output=True, text=True, timeout=120)
        _SUB = r.stdout.strip()
        if not _SUB:
            raise RuntimeError('az account show returned no subscription id: ' + scrub(r.stderr)[:500])
        _register_secret(_SUB, '<subscription-id>')
    return _SUB


def resource_id():
    return (f'/subscriptions/{subscription_id()}/resourceGroups/{RG}'
            f'/providers/Microsoft.DocumentDB/mongoClusters/{CLUSTER}')


def arm_url():
    return f'https://management.azure.com{resource_id()}?api-version={API_VERSION}'


# Exact Azure CLI command texts from the Learn overview page ("Enable full-text search" >
# "Azure CLI"), https://learn.microsoft.com/en-us/azure/documentdb/full-text-search-overview
LEARN_GET_STATE = r"""az rest --method get --url "$URL" \
  --query '{state:properties.provisioningState,features:properties.previewFeatures}' \
  --output json"""

LEARN_GET_BODY = r"""az rest --method get --url "$URL" \
  --query '{properties: {previewFeatures: [properties.previewFeatures[?@ != `"FullTextSearch"`] || `[]`, [`"FullTextSearch"`]][]}}' \
  --output json"""

LEARN_PATCH = 'az rest --method patch --url "$URL" --body "$BODY"'

SHOW_CMD = r"""az documentdb mongocluster show --resource-group "$MANAGED_RG" --name "$MANAGED_CLUSTER" --output json"""


def az_bash(cmd_text, extra_env=None, timeout=300):
    env = dict(os.environ)
    env['RESOURCE_ID'] = resource_id()
    env['URL'] = arm_url()
    env['MANAGED_RG'] = RG
    env['MANAGED_CLUSTER'] = CLUSTER
    if extra_env:
        env.update(extra_env)
    t0 = time.time()
    try:
        r = subprocess.run(['bash', '-c', cmd_text], capture_output=True, text=True, env=env,
                           timeout=timeout)
        rc, out, err = r.returncode, r.stdout, r.stderr
    except subprocess.TimeoutExpired as e:
        rc, out, err = 'timeout', (e.stdout or ''), (e.stderr or '') + f'\n<timeout after {timeout}s>'
        if isinstance(out, bytes):
            out = out.decode(errors='replace')
        if isinstance(err, bytes):
            err = err.decode(errors='replace')
    t1 = time.time()
    parsed = None
    if out and out.strip():
        try:
            parsed = json.loads(out)
        except Exception:
            parsed = None
    return {'started_utc': iso(t0), 'ended_utc': iso(t1), 'started_epoch': t0, 'ended_epoch': t1,
            'elapsed_s': round(t1 - t0, 3), 'returncode': rc,
            'stdout_json': parsed, 'stdout_raw': out if parsed is None else None, 'stderr': err,
            'stdout_text': out}


def az_vars_note():
    return {'URL': scrub(arm_url()), 'RESOURCE_ID': scrub(resource_id()),
            'MANAGED_RG': RG, 'MANAGED_CLUSTER': CLUSTER}


# ---------- Recorder ---------------------------------------------------------------

class Recorder:
    def __init__(self, out_name):
        self.path = os.path.join(HERE, out_name)
        self.steps = []
        self.lock = threading.Lock()

    def add(self, rec):
        with self.lock:
            self.steps.append(j(rec))
            self.save()
            return self.steps[-1]

    def save(self):
        tmp = self.path + '.tmp'
        with open(tmp, 'w') as f:
            json.dump(self.steps, f, indent=2)
        os.replace(tmp, self.path)

    def run(self, db, step, part, question, cmd, *, extra=False, oss_step=None, note=None,
            quiet=False, client_label=None, more=None):
        """Send one raw command with db.command(cmd); record exact command and raw reply/error."""
        rec = {'step': step, 'part': part, 'question': question, 'extra': extra,
               'driver_call': f'pymongo Database("{db.name}").command(<command>)'
                              + (f' on {client_label}' if client_label else ''),
               'command': cmd, 'at_utc': now_utc()}
        if oss_step:
            rec['oss_step'] = oss_step
        if note:
            rec['note'] = note
        if more:
            rec.update(more)
        t0 = time.time()
        rec['at_epoch'] = t0
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
                            'errorLabels': list(getattr(e, '_error_labels', []) or []) or None}
        rec['elapsed_s'] = round(time.time() - t0, 3)
        out = self.add(rec)
        if not quiet:
            body = out.get('response') if out['outcome'] == 'ok' else {k: v for k, v in out['error'].items() if k != 'raw'}
            print(f"[{step}] {out['outcome']} ({out['elapsed_s']}s): {json.dumps(body)[:700]}", flush=True)
        return out

    def az(self, step, part, question, cmd_text, *, extra_env=None, extra=False, note=None,
           quiet=False, record_env=None, more=None):
        res = az_bash(cmd_text, extra_env=extra_env)
        rec = {'step': step, 'part': part, 'question': question, 'extra': extra,
               'driver_call': 'bash -c <command> (Azure CLI ' + 'az rest' + ' / az documentdb)',
               'command': cmd_text, 'command_variables': az_vars_note(),
               'at_utc': res['started_utc'], 'ended_utc': res['ended_utc'],
               'at_epoch': res['started_epoch'], 'ended_epoch': res['ended_epoch'],
               'elapsed_s': res['elapsed_s'], 'returncode': res['returncode'],
               'outcome': 'ok' if res['returncode'] == 0 else 'error',
               'response': res['stdout_json'] if res['stdout_json'] is not None else res['stdout_raw'],
               'stderr': res['stderr']}
        if record_env:
            rec['command_variables'].update(record_env)
        if note:
            rec['note'] = note
        if more:
            rec.update(more)
        out = self.add(rec)
        if not quiet:
            print(f"[{step}] rc={out['returncode']} ({out['elapsed_s']}s): "
                  f"{json.dumps(out['response'])[:700]} | stderr: {out['stderr'][:300]!r}", flush=True)
        return out, res

    def note(self, step, part, question, driver_call, response, reading=None, extra=False,
             oss_step=None, more=None):
        rec = {'step': step, 'part': part, 'question': question, 'extra': extra,
               'driver_call': driver_call, 'at_utc': now_utc(), 'outcome': 'ok', 'response': response}
        if oss_step:
            rec['oss_step'] = oss_step
        if reading:
            rec['reading'] = reading
        if more:
            rec.update(more)
        out = self.add(rec)
        print(f"[{step}] {json.dumps(out['response'])[:700]}", flush=True)
        return out


# ---------- cluster monitor ----------------------------------------------------------

def show_fields(doc):
    p = (doc or {}).get('properties', {}) if isinstance(doc, dict) else {}
    return {'provisioningState': p.get('provisioningState'),
            'clusterStatus': p.get('clusterStatus'),
            'previewFeatures': p.get('previewFeatures', '<absent from show output>'),
            'lastModifiedAt': ((doc or {}).get('systemData') or {}).get('lastModifiedAt') if isinstance(doc, dict) else None}


class ClusterMonitor(threading.Thread):
    """Every `interval` s (anchored on `anchor`): Learn's check GET + az documentdb mongocluster show."""

    def __init__(self, rec, prefix, anchor, interval=30, offset=10, until_epoch=None, start_n=0):
        super().__init__(daemon=True)
        self.rec, self.prefix, self.anchor = rec, prefix, anchor
        self.interval, self.offset, self.until = interval, offset, until_epoch
        self.n = start_n
        self._stop_evt = threading.Event()
        self.last_tuple = None
        self.samples = []

    def stop(self):
        self._stop_evt.set()

    def sample(self, tag=''):
        n = self.n
        self.n += 1
        since = None
        g, gres = self.rec.az(f'{self.prefix}.{n:02d}.get', 'b',
                              'Learn check GET: provisioningState and previewFeatures (api-version 2024-07-01)',
                              LEARN_GET_STATE, quiet=True,
                              more={'since_patch_s': round(time.time() - self.anchor, 1) if self.anchor else None,
                                    'monitor_tag': tag})
        s_res = az_bash(SHOW_CMD)
        fields = show_fields(s_res['stdout_json'])
        tup = json.dumps(fields, sort_keys=True)
        changed = tup != self.last_tuple
        self.last_tuple = tup
        rec = {'step': f'{self.prefix}.{n:02d}.show', 'part': 'b', 'extra': False,
               'question': 'az documentdb mongocluster show: provisioningState, clusterStatus, previewFeatures',
               'driver_call': 'bash -c <command> (Azure CLI az documentdb)', 'command': SHOW_CMD,
               'command_variables': {'MANAGED_RG': RG, 'MANAGED_CLUSTER': CLUSTER},
               'at_utc': s_res['started_utc'], 'ended_utc': s_res['ended_utc'],
               'at_epoch': s_res['started_epoch'], 'elapsed_s': s_res['elapsed_s'],
               'since_patch_s': round(s_res['started_epoch'] - self.anchor, 1) if self.anchor else None,
               'returncode': s_res['returncode'], 'outcome': 'ok' if s_res['returncode'] == 0 else 'error',
               'response_fields': fields, 'fields_changed_since_previous_sample': changed,
               'stderr': s_res['stderr'], 'monitor_tag': tag}
        if changed or s_res['returncode'] != 0:
            rec['response'] = s_res['stdout_json'] if s_res['stdout_json'] is not None else s_res['stdout_raw']
        out = self.rec.add(rec)
        line = {'n': n, 'since_patch_s': out.get('since_patch_s'), 'get': g.get('response'),
                'show': out['response_fields'], 'changed': changed}
        self.samples.append(line)
        print(f"[{self.prefix}.{n:02d}] {json.dumps(line)}", flush=True)
        return line

    def run(self):
        k = 0
        while not self._stop_evt.is_set():
            target = self.anchor + self.offset + k * self.interval
            now = time.time()
            if target < now - self.interval:   # skip slots already past
                k = int((now - self.anchor - self.offset) // self.interval) + 1
                continue
            if self.until and target > self.until:
                break
            if self._stop_evt.wait(max(0, target - time.time())):
                break
            try:
                self.sample()
            except Exception as e:  # keep monitoring
                print(f'[{self.prefix}] monitor error {type(e).__name__}: {scrub(str(e))[:300]}', flush=True)
            k += 1


# ---------- test data and command builders -------------------------------------------

UTC = datetime.timezone.utc

# Learn "Structured and text search" sample documents, plus a 3-dimensional `embedding`
# field for the hybrid step (the field is not mapped in the search index).
DOCS = [
    {'_id': 1, 'title': 'Bracket controller', 'description': 'Steel mounting bracket for a controller',
     'partNumber': 'SKU-BRACKET-001', 'category': 'hardware', 'price': 49.0, 'inStock': True,
     'publishedAt': datetime.datetime(2026, 9, 1, tzinfo=UTC), 'details': {'region': 'west'},
     'embedding': [1.0, 0.0, 0.0]},
    {'_id': 2, 'title': 'Bracket assembly', 'description': 'Heavy-duty bracket for an industrial controller',
     'partNumber': 'SKU-BRACKET-002', 'category': 'hardware', 'price': 129.0, 'inStock': True,
     'publishedAt': datetime.datetime(2026, 10, 1, tzinfo=UTC), 'details': {'region': 'east'},
     'embedding': [0.0, 1.0, 0.0]},
    {'_id': 3, 'title': 'Lightweight bracket', 'description': 'Compact bracket for a controller',
     'partNumber': 'SKU-BRACKET-003', 'category': 'accessories', 'price': 29.0, 'inStock': False,
     'publishedAt': datetime.datetime(2026, 10, 15, tzinfo=UTC), 'details': {'region': 'west'},
     'embedding': [0.6, 0.8, 0.0]},
]

IDX_NAME = 'idx_products_filters'
IDX_DEF = {
    'name': IDX_NAME,
    'definition': {'mappings': {'dynamic': False, 'fields': {
        'title': {'type': 'string'},
        'description': {'type': 'string'},
        'partNumber': {'type': 'token'},
        'category': {'type': 'token'},
        'price': {'type': 'number', 'representation': 'double'},
        'inStock': {'type': 'boolean'},
        'publishedAt': {'type': 'date'},
        'details': {'type': 'document', 'fields': {'region': {'type': 'token'}}},
    }}},
}


def create_search_index_cmd():
    return {'createSearchIndexes': COLL, 'indexes': [IDX_DEF]}


def agg(pipeline, coll=COLL):
    return {'aggregate': coll, 'pipeline': pipeline, 'cursor': {}}


def list_search_indexes_cmd(name=IDX_NAME):
    return agg([{'$listSearchIndexes': {'name': name} if name else {}}])


def batch(rec):
    if rec.get('outcome') != 'ok':
        return None
    return rec['response'].get('cursor', {}).get('firstBatch')


def index_ready(rec):
    b = batch(rec)
    if not b:
        return False
    d = b[0]
    return d.get('status') == 'READY' and d.get('queryable') is True
