"""Step (a) plus pre-enable baseline: database mt_fts only; no cluster configuration change."""
import json
import sys

from common import (COLL, DB_NAME, DOCS, IDX_NAME, LEARN_GET_STATE, SHOW_CMD, Recorder, agg,
                    az_bash, create_search_index_cmd, get_client, j, show_fields)

rec = Recorder('steps_a_pre.json')
client = get_client()
admin = client['admin']
db = client[DB_NAME]

rec.run(admin, 'a0.hello', 'setup', 'hello on the plain host (engine identity before enabling)', {'hello': 1})
rec.run(admin, 'a0.buildInfo', 'setup', 'buildInfo before enabling', {'buildInfo': 1})

# Cluster configuration before enabling (read-only)
rec.az('a0.az.get_state', 'b', 'Learn check GET before the PATCH: provisioningState and previewFeatures',
       LEARN_GET_STATE)
s = az_bash(SHOW_CMD)
rec.add({'step': 'a0.az.show', 'part': 'b', 'extra': False,
         'question': 'az documentdb mongocluster show before the PATCH (full, masked)',
         'driver_call': 'bash -c <command> (Azure CLI az documentdb)', 'command': SHOW_CMD,
         'command_variables': {'MANAGED_RG': 'documentdb-samples-rg', 'MANAGED_CLUSTER': 'ddb-samples-shared'},
         'at_utc': s['started_utc'], 'elapsed_s': s['elapsed_s'], 'returncode': s['returncode'],
         'outcome': 'ok' if s['returncode'] == 0 else 'error',
         'response_fields': show_fields(s['stdout_json']),
         'response': s['stdout_json'] if s['stdout_json'] is not None else s['stdout_raw'],
         'stderr': s['stderr']})
print('[a0.az.show]', json.dumps(j(show_fields(s['stdout_json']))))

r = rec.run(admin, 'a1.db_absent', 'setup', 'mt_fts must not exist before the test',
            {'listDatabases': 1, 'nameOnly': True, 'filter': {'name': DB_NAME}})
if r['outcome'] == 'ok' and r['response'].get('databases'):
    print('mt_fts already exists; stopping so nothing else is touched')
    sys.exit(2)

rec.run(db, 'a2.create', 'setup', 'create the small collection products', {'create': COLL})
rec.run(db, 'a3.insert', 'setup',
        'insert the three Learn structured-search sample documents (plus a 3-d embedding field)',
        {'insert': COLL, 'documents': DOCS, 'ordered': True})

rec.run(db, 'a4.createSearchIndexes.pre', 'a',
        '(a) createSearchIndexes before FullTextSearch is enabled: exact error',
        create_search_index_cmd(), oss_step='02b-createSearchIndexes-static-mapping')

# Extras: other search surfaces before enabling, for the pre/post and OSS comparison
rec.run(db, 'a5x.listSearchIndexes.pre', 'a', '$listSearchIndexes before enabling',
        agg([{'$listSearchIndexes': {}}]), extra=True, oss_step='04-listSearchIndexes')
rec.run(db, 'a6x.search_text.pre', 'a', '$search text before enabling',
        agg([{'$search': {'index': IDX_NAME, 'text': {'query': 'bracket', 'path': 'title'}}},
             {'$limit': 20}, {'$project': {'_id': 0, 'title': 1, 'score': {'$meta': 'searchScore'}}}]),
        extra=True, oss_step='03-search-text')
rec.run(db, 'a7x.rankFusion.pre', 'a', '$rankFusion (open-source test form) before enabling',
        agg([{'$rankFusion': {'input': {'pipelines': {'byId': [{'$sort': {'_id': 1}}],
                                                      'byTitle': [{'$sort': {'title': 1}}]}}}},
             {'$limit': 3}]), extra=True, oss_step='07-rankFusion')
rec.run(db, 'a8x.searchMeta.pre', 'a', '$searchMeta before enabling',
        agg([{'$searchMeta': {'index': IDX_NAME, 'text': {'query': 'bracket', 'path': 'description'}}}]),
        extra=True)
rec.run(db, 'a9x.createSearchIndexes.dynamic.pre', 'a',
        'createSearchIndexes with mappings.dynamic true before enabling (does validation run before the feature gate?)',
        {'createSearchIndexes': COLL, 'indexes': [{'name': 'fts_dynamic', 'definition': {'mappings': {'dynamic': True}}}]},
        extra=True, oss_step='02-createSearchIndexes')
rec.run(db, 'a10x.listIndexes.pre', 'a', 'listIndexes on products before enabling (baseline)',
        {'listIndexes': COLL}, extra=True)
client.close()
print('done')
