"""Conclusions and notes for the m-fts report (imported by finalize.py)."""


def build(monitor_last_since_s, final_state):
    return [
        {'question': '(a) What does createSearchIndexes return on a small collection before FullTextSearch is enabled?',
         'answer': ('Code 115, codeName CommandNotSupported, errmsg "Search index creation is not supported yet", no errorLabels '
                    '(step a4 at 2026-11-25T21:48:43.717Z, 3-document collection mt_fts.products, static mapping from the Learn '
                    'structured-search page). A mappings.dynamic true definition gets the identical reply (a9x), so the feature gate runs '
                    'before definition validation. Other surfaces before enabling: $listSearchIndexes 115 "$listSearchIndexes stage is not '
                    'enabled", $search text 40324 UnrecognizedCommand "Unrecognized $search option: text", $searchMeta 115 "Stage $searchMeta '
                    'is not supported yet in native pipeline", $rankFusion 40324 "Pipeline stage name not recognized: $rankFusion".'),
         'vs_open_source': 'different', 'confidence': 'observed',
         'detail_vs_open_source': ('Same code 115 and codeName; the open-source gateway (0.117 and 1.2.0) says "Command \'createSearchIndexes\' '
                                   'not supported.". The $listSearchIndexes, $search text and $rankFusion replies are identical to open source.')},
        {'question': '(b) What did the Learn Azure CLI enablement return, and when?',
         'answer': ('Learn command 1 returned {"state":"Succeeded","features":null}; command 2 built BODY {"properties":{"previewFeatures":'
                    '["FullTextSearch"]}} (nothing else to preserve); command 3, az rest --method patch --url "$URL" --body "$BODY" with '
                    'api-version 2024-07-01, was sent at 2026-11-25T21:50:25.938Z and returned rc 0 at 21:50:26.818Z (0.88 s) with the full '
                    'resource: properties.provisioningState "Updating", clusterStatus "Updating", previewFeatures ["FullTextSearch"], '
                    'systemData.lastModifiedAt 21:50:26.4164906Z, empty stderr. Learn command 4 (check), sent at +0.0 s alongside attempt 0 and '
                    'answered by +1.2 s: {"state":"Updating","features":["FullTextSearch"]}.'),
         'vs_open_source': 'n/a', 'confidence': 'observed'},
        {'question': '(b) How did provisioningState and properties.previewFeatures evolve over the following minutes?',
         'answer': ('properties.previewFeatures read ["FullTextSearch"] in the PATCH response and in every later sample, in both the Learn '
                    'az rest GET (2024-07-01) and az documentdb mongocluster show (extension 1.0.0); before the PATCH the GET returned '
                    'features null and show had no previewFeatures key. provisioningState (and clusterStatus in show) read "Updating" in the '
                    'samples sent at +0, +30, +60, +90, +120 and +150 s (show about 1 s later each time) and "Succeeded"/"Ready" from the '
                    'sample sent at +180.0 s (show +180.8 s); every sample after that (to +210.6 s, then '
                    f'+360.9 s to +{monitor_last_since_s} s, no samples in between) stayed Succeeded/Ready with systemData.lastModifiedAt '
                    f'unchanged at 21:50:26.4164906Z. Final check: {final_state}. So the ARM update ran for 151 to 181 s.'),
         'vs_open_source': 'n/a', 'confidence': 'observed'},
        {'question': '(c) Is code 115 also returned during the activation window, or a different error?',
         'answer': ('Both, one after the other. Attempts at +0, +30, +60 and +90 s returned 115 CommandNotSupported "Search index creation '
                    'is not supported yet", identical to the not-enabled reply. Attempts at +120, +150 and +180 s returned a different code '
                    'with the same message: 67 CannotCreateIndex "Search index creation is not supported yet". No reply carried errorLabels. '
                    'The 115 and the first two 67 replies came while the cluster reported Updating; the 67 replies at +180.0 s and +180.1 s came '
                    'at the same moment as the first Learn GET that returned Succeeded (sent at +180.0 s), so Succeeded can precede '
                    'data-plane readiness. '
                    'The persistent client and a fresh client got identical replies in every slot. So "treat 115 as not enabled yet" is '
                    'incomplete: during activation 67 with this errmsg also means "not active yet", and because 67 is also the code for an '
                    'invalid definition (x1), a retry loop should match the errmsg "Search index creation is not supported yet" (with code '
                    '115 or 67) rather than key on the code, and keep retrying for a short while after provisioningState reads Succeeded.'),
         'vs_open_source': 'different', 'confidence': 'observed',
         'detail_vs_open_source': 'The open-source gateway has no activation and always returns 115 "Command \'createSearchIndexes\' not supported.".'},
        {'question': '(c) How long did activation take?',
         'answer': ('About 3.5 minutes. The first successful createSearchIndexes was attempt 7 at +210.0 s (2026-11-25T21:53:56.828Z) after '
                    'the PATCH returned; the attempts at +180.0 s and +180.1 s still failed (67), so activation completed between +180.1 s and '
                    '+210.0 s, 0 to 30 s after provisioningState first read Succeeded (Learn GET sent at +180.0 s). The 115 to 67 switch '
                    'happened between +90.1 s and '
                    '+120.0 s. Learn says to wait 10 minutes; on this M30 single-shard cluster without HA the feature was usable after '
                    '3 min 30 s. This is one observation at a 30-s cadence, not a service guarantee.'),
         'vs_open_source': 'n/a', 'confidence': 'observed'},
        {'question': 'Do clients have to reconnect after activation?',
         'answer': ('No. The successful call at +210 s came from the persistent client whose connection was opened before the PATCH: '
                    'gateway connectionId 174955255 both before the PATCH and after the success. No network error, disconnect or '
                    'server-selection error occurred during activation, and fresh clients never got a different answer.'),
         'vs_open_source': 'n/a', 'confidence': 'observed'},
        {'question': 'Extra: when does $listSearchIndexes start working during activation?',
         'answer': ('115 "$listSearchIndexes stage is not enabled" until +91.2 s; from +121.2 s ok with an empty firstBatch, the same '
                    'moment createSearchIndexes switched from 115 to 67, about 90 s before index creation was accepted. A working '
                    '$listSearchIndexes therefore does not prove that createSearchIndexes will be accepted.'),
         'vs_open_source': 'different', 'confidence': 'observed',
         'detail_vs_open_source': 'Same 115 message as open source until +91 s; open source never enables the stage.'},
        {'question': '(d) $listSearchIndexes until status READY and queryable true: documents and time',
         'answer': ('The first $listSearchIndexes {name: "idx_products_filters"}, sent as soon as createSearchIndexes returned (that call '
                    'took 1.08 s; 2026-11-25T21:53:57.921Z, +211.1 s), already returned one document: {id: "225", name: "idx_products_filters", '
                    'status: "READY", queryable: true, latestDefinition: <the submitted mappings>}. The createSearchIndexes reply was '
                    '{raw: {defaultShard: {numIndexesBefore: 1, numIndexesAfter: 2, createdCollectionAutomatically: false, ok: 1}}, ok: 1}. '
                    'A $search sent 0.1 s after createSearchIndexes returned already returned results. Collection of 3 documents; build time on large '
                    'collections was not measured.'),
         'vs_open_source': 'different', 'confidence': 'observed',
         'detail_vs_open_source': 'The open-source gateway rejects $listSearchIndexes with 115.'},
        {'question': '(d) Does a $search text query work after activation?',
         'answer': ('Yes. $search {index: "idx_products_filters", text: {query: "bracket", path: "title"}} + $limit + $project searchScore '
                    'returned the three titles, each with BM25 score 0.13353. Extras: "industrial controller" on description ranked document '
                    '2 (1.043) over 3 (0.143) and 1 (0.134) with the default any-term matching; matchCriteria "all" over title and '
                    'description returned only document 2.'),
         'vs_open_source': 'different', 'confidence': 'observed',
         'detail_vs_open_source': 'The open-source gateway rejects $search text with 40324 "Unrecognized $search option: text".'},
        {'question': '(d) Does compound with must, should, filter and mustNot work?',
         'answer': ('Yes. The Learn structured-search query (must text "bracket controller" over title and description with matchCriteria '
                    'all; should phrase slop 0; filter equals inStock true, range price 20 to 100, in category, exists publishedAt; mustNot '
                    'equals details.region "retired") returned only "Bracket controller" (SKU-BRACKET-001, 49.0, score 4.966), exactly the '
                    'result Learn states. An extra mustNot on region "west" excluded documents 1 and 3, so mustNot is enforced.'),
         'vs_open_source': 'not_tested_locally', 'confidence': 'observed'},
        {'question': '(d) compound.minimumShouldMatch',
         'answer': ('Unsupported, as Learn says: code 115 CommandNotSupported "\'compound.minimumShouldMatch\' is not supported yet.", no '
                    'errorLabels (step d4 at 21:56:30.255Z).'),
         'vs_open_source': 'not_tested_locally', 'confidence': 'observed'},
        {'question': '(d) $searchMeta',
         'answer': ('Unsupported before and after enabling, with or without count: code 115 CommandNotSupported "Stage $searchMeta is not '
                    'supported yet in native pipeline", no errorLabels.'),
         'vs_open_source': 'not_tested_locally', 'confidence': 'observed'},
        {'question': '(d) $rankFusion',
         'answer': ('Unsupported before and after enabling: code 40324 UnrecognizedCommand "Pipeline stage name not recognized: $rankFusion" '
                    'for both the open-source test form ($sort pipelines) and a vector plus keyword $search form.'),
         'vs_open_source': 'same', 'confidence': 'observed',
         'detail_vs_open_source': 'Identical code and message to open-source step 07 on 0.117 and 1.2.0.'},
        {'question': '(d) Hybrid: vector-ivf index plus the search index through the Learn $unionWith RRF pipeline',
         'answer': ('Works in one round trip. With a vector-ivf index (3 dimensions, COS, numLists 1) on embedding, userQuery "industrial", '
                    'qv [0.9, 0.1, 0.0] and k 60, the Learn pipeline (vector $search, $group/$unwind/$project rrf, then $unionWith a keyword '
                    '$search branch, final $group/$sort/$limit) returned document 2 (0.032266), 1 (0.016393), 3 (0.016129), identical to '
                    'the page\'s client-side rrf() over the separate queries (keyword: only 2; vector: 1, 3, 2). $search is accepted inside '
                    '$unionWith, and the vector branch carried the full documents (titles) without returnStoredSource. Only the search index '
                    'name differs from the page (idx_products_filters instead of idx_description_fts).'),
         'vs_open_source': 'not_tested_locally', 'confidence': 'observed',
         'detail_vs_open_source': 'Not run locally; its keyword branch is rejected there with 40324, so it cannot run on open source.'},
        {'question': 'Extra: search-index lifecycle commands',
         'answer': ('dropIndexes {index: "idx_products_filters"} drops a search index (ok 1, nIndexesWas 3) and $listSearchIndexes is then '
                    'empty; re-creating it succeeds and is READY immediately (new id "227"). dropSearchIndex and updateSearchIndex are not '
                    'commands: 59 CommandNotFound "Command \'dropSearchIndex\' not found." and "Command \'updateSearchIndex\' not found.", so '
                    'driver helpers drop_search_index/update_search_index fail. mappings.dynamic true after enabling: 67 CannotCreateIndex '
                    '"Error in specification { ... }:mappings.dynamic is not supported in search indexes yet" (Learn quotes the message '
                    'without the prefix and with a period). listIndexes does not list the search index, but numIndexesBefore/After and '
                    'nIndexesWas count it.'),
         'vs_open_source': 'not_tested_locally', 'confidence': 'observed'},
        {'question': 'Extra: what does $search return without a $project?',
         'answer': ('Whole documents plus an internal field __cosmos_meta__: {score: <BM25 score>} (x6). Agents that pass raw $search '
                    'output on should project it away or read the score with {$meta: "searchScore"}.'),
         'vs_open_source': 'not_tested_locally', 'confidence': 'observed'},
        {'question': 'Did enabling the preview change the reported engine?',
         'answer': ('No. hello after enabling still reports maxWireVersion 25, internal.documentdb_versions ["2.2-1","2.3.0","12.1-1"], kind '
                    'azuredocumentdb, and buildInfo 8.0.0.'),
         'vs_open_source': 'n/a', 'confidence': 'observed'},
        {'question': 'Does seeing FullTextSearch in the resource configuration mean activation has finished (Learn warning)?',
         'answer': ('No, confirmed. previewFeatures showed ["FullTextSearch"] in the PATCH response at +0 s, but createSearchIndexes failed '
                    'until +210 s. provisioningState "Succeeded" is a close but not exact readiness signal: the GET sent at +180.0 s already '
                    'read Succeeded while createSearchIndexes at +180.0 s and +180.1 s still returned 67, and the next attempt, 30 s later, '
                    'succeeded. Retrying createSearchIndexes is the reliable check.'),
         'vs_open_source': 'n/a', 'confidence': 'observed'},
    ]


NOTES = ('Phase 2 run on 2026-11-25. The only cluster configuration change was the FullTextSearch preview PATCH, which was left enabled. '
         'Every data-plane step ran in database mt_fts, which did not exist at the start (a1), held one collection (products: the three '
         'Learn structured-search sample documents plus a 3-d embedding field), and was dropped at the end (z1) and confirmed absent (z2). '
         'Steps marked extra go beyond the stage spec but stay inside mt_fts: a5x-a10x (pre-enable surfaces), c.NN.fresh and c.NN.listx '
         '(fresh-client and $listSearchIndexes probes in each 30-s slot), d0x, d2x, d2y, d3x, d5x, d8x and x1-x6 (lifecycle). The 30-s '
         'schedule was anchored on the PATCH return time and kept to within 1 s; no --continue segment was needed. Cluster samples have a '
         'gap from +210.6 s to +360.9 s between the two monitor processes. Learn fixes suggested by these observations: document both '
         'activation-window replies (115 then 67 CannotCreateIndex, same errmsg) next to the enablement steps; the 10-minute wait was 3.5 '
         'minutes here, and provisioningState Succeeded came up to 30 s before createSearchIndexes was accepted; the dynamic-mapping error carries code 67 and an "Error in '
         'specification ...:" prefix; dropSearchIndex/updateSearchIndex return 59, so name dropIndexes explicitly for drivers; un-projected '
         '$search results carry __cosmos_meta__; the compatibility row marking $listSearchIndexes unsupported is stale (it works).')
