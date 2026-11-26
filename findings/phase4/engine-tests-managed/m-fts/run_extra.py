"""Extras inside mt_fts after step (d): search-index lifecycle (update, dropIndexes, recreate,
dropSearchIndex) and the documented dynamic-mapping error now that the feature is active."""
import time

from common import (COLL, DB_NAME, IDX_DEF, IDX_NAME, Recorder, agg, create_search_index_cmd,
                    get_client, index_ready, list_search_indexes_cmd, now_utc)

rec = Recorder('steps_extra.json')
client = get_client(appname='mt-fts-extra')
db = client[DB_NAME]
LIST_ALL = agg([{'$listSearchIndexes': {}}])

rec.run(db, 'x1.createSearchIndexes.dynamic', 'extra',
        'createSearchIndexes with mappings.dynamic true after enabling (Learn documents the error text)',
        {'createSearchIndexes': COLL, 'indexes': [{'name': 'fts_dynamic', 'definition': {'mappings': {'dynamic': True}}}]},
        extra=True)
rec.run(db, 'x2.updateSearchIndex', 'extra', 'updateSearchIndex (Learn: dedicated update APIs not supported)',
        {'updateSearchIndex': COLL, 'name': IDX_NAME, 'definition': IDX_DEF['definition']}, extra=True)
rec.run(db, 'x3.dropIndexes_search_index', 'extra', 'dropIndexes with the search index name (Learn: the way to drop one)',
        {'dropIndexes': COLL, 'index': IDX_NAME}, extra=True)
rec.run(db, 'x3b.listSearchIndexes', 'extra', '$listSearchIndexes after dropIndexes', LIST_ALL, extra=True)
c = rec.run(db, 'x4.createSearchIndexes.again', 'extra', 'createSearchIndexes again (feature already active)',
            create_search_index_cmd(), extra=True)
t_create = time.time()
r = rec.run(db, 'x4b.listSearchIndexes', 'extra', '$listSearchIndexes right after re-creation',
            list_search_indexes_cmd(), extra=True)
n = 0
while not index_ready(r) and n < 40:
    time.sleep(3)
    n += 1
    r = rec.run(db, f'x4b.{n:02d}.listSearchIndexes', 'extra', '$listSearchIndexes poll until READY',
                list_search_indexes_cmd(), extra=True, quiet=True)
rec.run(db, 'x4c.search_text', 'extra', '$search text against the re-created index',
        agg([{'$search': {'index': IDX_NAME, 'text': {'query': 'bracket', 'path': 'title'}}},
             {'$limit': 20}, {'$project': {'_id': 0, 'title': 1, 'score': {'$meta': 'searchScore'}}}]), extra=True)
rec.run(db, 'x5.dropSearchIndex', 'extra', 'dropSearchIndex command (what driver drop_search_index helpers send)',
        {'dropSearchIndex': COLL, 'name': IDX_NAME}, extra=True)
rec.run(db, 'x5b.listSearchIndexes', 'extra', '$listSearchIndexes after dropSearchIndex', LIST_ALL, extra=True)
rec.run(db, 'x6.search_text_no_index', 'extra', '$search text after the search index is gone (if it was dropped)',
        agg([{'$search': {'index': IDX_NAME, 'text': {'query': 'bracket', 'path': 'title'}}}, {'$limit': 5}]),
        extra=True)
client.close()
print('extras done', now_utc())
