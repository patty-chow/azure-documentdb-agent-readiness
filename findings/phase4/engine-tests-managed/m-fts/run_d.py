"""Step (d) after createSearchIndexes succeeded, plus cleanup (drop mt_fts). The cluster monitor keeps
sampling every 30 s (same schedule anchored on the PATCH) until about 12 minutes after the PATCH.
The FullTextSearch preview feature is left enabled."""
import json
import os
import time

from common import (COLL, DB_NAME, HERE, IDX_NAME, LEARN_GET_STATE, ClusterMonitor, Recorder, agg,
                    batch, get_client, index_ready, list_search_indexes_cmd, now_utc)

STATE_PATH = os.path.join(HERE, 'state_c.json')
st = json.load(open(STATE_PATH))
t0 = st['t0']
assert st.get('success'), 'createSearchIndexes has not succeeded yet'
start = time.time()
MON_UNTIL = min(t0 + 12 * 60, start + 8 * 60 + 40)

rec = Recorder('steps_d.json')

client = get_client(appname='mt-fts-d')
db = client[DB_NAME]
admin = client['admin']

# d1: confirm READY/queryable (first observed in d1.00 right after creation)
r = rec.run(db, 'd1.r.listSearchIndexes', 'd', '$listSearchIndexes (named) at the start of step d',
            list_search_indexes_cmd())
if not index_ready(r):
    for n in range(1, 120):
        time.sleep(3)
        r = rec.run(db, f'd1.r{n:02d}.listSearchIndexes', 'd', '$listSearchIndexes poll until READY',
                    list_search_indexes_cmd(), quiet=True)
        if index_ready(r):
            break

PROJ = {'$project': {'_id': 0, 'title': 1, 'score': {'$meta': 'searchScore'}}}

# d2: $search text (keyword page form, path title) + two extras on description
rec.run(db, 'd2.search_text', 'd', '$search text query (BM25 keyword page form)',
        agg([{'$search': {'index': IDX_NAME, 'text': {'query': 'bracket', 'path': 'title'}}},
             {'$limit': 20}, PROJ]), oss_step='03-search-text')
rec.run(db, 'd2x.search_text_any', 'd', 'extra: $search text "industrial controller" on description (matchCriteria default)',
        agg([{'$search': {'index': IDX_NAME, 'text': {'query': 'industrial controller', 'path': 'description'}}},
             {'$limit': 20}, {'$project': {'_id': 1, 'description': 1, 'score': {'$meta': 'searchScore'}}}]), extra=True)
rec.run(db, 'd2y.search_text_all', 'd', 'extra: same query with matchCriteria "all" across two paths',
        agg([{'$search': {'index': IDX_NAME, 'text': {'query': 'industrial controller',
                                                      'path': ['title', 'description'], 'matchCriteria': 'all'}}},
             {'$limit': 20}, {'$project': {'_id': 1, 'description': 1, 'score': {'$meta': 'searchScore'}}}]), extra=True)

# d3: compound with must, should, filter and mustNot (exactly the Learn structured-search query)
compound_query = [
    {'$search': {'index': IDX_NAME, 'compound': {
        'must': [{'text': {'query': 'bracket controller', 'path': ['title', 'description'], 'matchCriteria': 'all'}}],
        'should': [{'phrase': {'query': 'bracket controller', 'path': 'title', 'slop': 0}}],
        'filter': [{'equals': {'path': 'inStock', 'value': True}},
                   {'range': {'path': 'price', 'gte': 20, 'lte': 100}},
                   {'in': {'path': 'category', 'value': ['hardware', 'accessories']}},
                   {'exists': {'path': 'publishedAt'}}],
        'mustNot': [{'equals': {'path': 'details.region', 'value': 'retired'}}]}}},
    {'$limit': 10},
    {'$project': {'_id': 0, 'title': 1, 'partNumber': 1, 'price': 1, 'inStock': 1, 'score': {'$meta': 'searchScore'}}},
]
rec.run(db, 'd3.compound', 'd', 'compound with must, should, filter and mustNot (Learn structured-search query)',
        agg(compound_query))
rec.run(db, 'd3x.compound_mustNot_effective', 'd',
        'extra: compound must text "bracket" + mustNot equals details.region "west" (mustNot that excludes something)',
        agg([{'$search': {'index': IDX_NAME, 'compound': {
            'must': [{'text': {'query': 'bracket', 'path': 'description'}}],
            'mustNot': [{'equals': {'path': 'details.region', 'value': 'west'}}]}}},
            {'$limit': 10}, {'$project': {'_id': 1, 'title': 1, 'details': 1, 'score': {'$meta': 'searchScore'}}}]),
        extra=True)

# d4: compound.minimumShouldMatch (documented as unsupported)
rec.run(db, 'd4.compound_minimumShouldMatch', 'd', 'compound.minimumShouldMatch (expected unsupported)',
        agg([{'$search': {'index': IDX_NAME, 'compound': {
            'should': [{'text': {'query': 'steel', 'path': 'description'}},
                       {'text': {'query': 'compact', 'path': 'description'}}],
            'minimumShouldMatch': 1}}},
            {'$limit': 10}, PROJ]))

# d5: $searchMeta (documented as unsupported)
rec.run(db, 'd5.searchMeta', 'd', '$searchMeta (expected unsupported)',
        agg([{'$searchMeta': {'index': IDX_NAME, 'text': {'query': 'bracket', 'path': 'description'}}}]))
rec.run(db, 'd5x.searchMeta_count', 'd', 'extra: $searchMeta with count total',
        agg([{'$searchMeta': {'index': IDX_NAME, 'count': {'type': 'total'},
                              'text': {'query': 'bracket', 'path': 'description'}}}]), extra=True)

# d6a: $rankFusion, same form as the open-source test
rec.run(db, 'd6a.rankFusion', 'd', '$rankFusion (open-source test form) after enabling (expected unsupported)',
        agg([{'$rankFusion': {'input': {'pipelines': {'byId': [{'$sort': {'_id': 1}}],
                                                      'byTitle': [{'$sort': {'title': 1}}]}}}},
             {'$limit': 3}]), oss_step='07-rankFusion')

# d7: hybrid with a vector-ivf index and the search index
user_query = 'industrial'
qv = [0.9, 0.1, 0.0]
K = 60
TOP_N = 10
rec.run(db, 'd7a.create_vector_ivf', 'd', 'create a vector-ivf index on embedding (3 dimensions, COS, numLists 1)',
        {'createIndexes': COLL, 'indexes': [{'name': 'desc_ivf', 'key': {'embedding': 'cosmosSearch'},
                                             'cosmosSearchOptions': {'kind': 'vector-ivf', 'numLists': 1,
                                                                     'dimensions': 3, 'similarity': 'COS'}}]})
rec.run(db, 'd7b.listIndexes', 'd', 'extra: listIndexes on products (is the search index listed?)',
        {'listIndexes': COLL}, extra=True)
kw = rec.run(db, 'd7c.keyword_query', 'd', 'hybrid Step 2 keyword query alone (page form)',
             agg([{'$search': {'index': IDX_NAME, 'text': {'query': user_query, 'path': 'description'}}},
                  {'$limit': 50}, {'$project': {'_id': 1, 'kw': {'$meta': 'searchScore'}}}]))
vec = rec.run(db, 'd7d.vector_query', 'd', 'hybrid Step 2 vector query alone (page form, IVF)',
              agg([{'$search': {'cosmosSearch': {'path': 'embedding', 'vector': qv, 'k': 50}}},
                   {'$project': {'_id': 1, 'vec': {'$meta': 'searchScore'}}}]))


def rrf(lists, k=60):
    scores = {}
    for lst in lists:
        for rank, d in enumerate(lst):
            scores[d['_id']] = scores.get(d['_id'], 0) + 1 / (k + rank + 1)
    return [{'_id': i, 'score': s} for i, s in sorted(scores.items(), key=lambda kv: -kv[1])][:10]


client_side = rrf([batch(kw) or [], batch(vec) or []], K)
rec.note('d7e.client_side_rrf', 'd', 'client-side RRF of d7c and d7d (page Step 3 rrf(), k=60), computed locally',
         'python port of the page rrf() helper over the two firstBatch lists', client_side)


def rrf_branch():
    return [{'$group': {'_id': None, 'hits': {'$push': '$$ROOT'}}},
            {'$unwind': {'path': '$hits', 'includeArrayIndex': 'rank'}},
            {'$project': {'_id': '$hits._id', 'title': '$hits.title',
                          'rrf': {'$divide': [1, {'$add': ['$rank', K, 1]}]}}}]


hybrid_pipeline = (
    [{'$search': {'cosmosSearch': {'path': 'embedding', 'vector': qv, 'k': 50}}}] + rrf_branch() +
    [{'$unionWith': {'coll': COLL, 'pipeline':
        [{'$search': {'index': IDX_NAME, 'text': {'query': user_query, 'path': 'description'}}},
         {'$limit': 50}] + rrf_branch()}},
     {'$group': {'_id': '$_id', 'title': {'$first': '$title'}, 'score': {'$sum': '$rrf'}}},
     {'$sort': {'score': -1}},
     {'$limit': TOP_N}])
rec.run(db, 'd7f.hybrid_unionWith_rrf', 'd',
        'hybrid: server-side RRF with $unionWith (Learn hybrid page pipeline; index name idx_products_filters)',
        agg(hybrid_pipeline),
        note='Pipeline copied from the Learn hybrid page "Server-side RRF with $unionWith"; only the search index '
             'name differs (idx_products_filters, which maps description as string). userQuery="industrial", '
             'qv=[0.9, 0.1, 0.0], k=60, topN=10.')
rec.run(db, 'd6b.rankFusion_hybrid', 'd', '$rankFusion over the vector and keyword pipelines (expected unsupported)',
        agg([{'$rankFusion': {'input': {'pipelines': {
            'vector': [{'$search': {'cosmosSearch': {'path': 'embedding', 'vector': qv, 'k': 50}}}],
            'keyword': [{'$search': {'index': IDX_NAME, 'text': {'query': user_query, 'path': 'description'}}},
                        {'$limit': 50}]}}}},
             {'$limit': 10}]))

rec.run(db, 'd8x.listSearchIndexes_all', 'd', 'extra: $listSearchIndexes {} (all) before cleanup',
        agg([{'$listSearchIndexes': {}}]), extra=True)

client.close()
print('step d done', now_utc(), flush=True)
