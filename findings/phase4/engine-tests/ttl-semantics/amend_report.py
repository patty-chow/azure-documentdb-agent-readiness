import json, os, re
HERE = os.path.dirname(os.path.abspath(__file__))
p = os.path.join(HERE, "report.json"); r = json.load(open(p))
excerpt = open(os.path.join(HERE, "pglog_ttl_excerpt.txt")).read().splitlines()
cron_starts = [re.search(r"(\d{4}-\d\d-\d\d \d\d:\d\d:\d\d\.\d+) UTC .*cron job 1 starting", l).group(1) for l in excerpt if "cron job 1 starting" in l]
cron_done = [re.search(r"(\d{4}-\d\d-\d\d \d\d:\d\d:\d\d\.\d+) UTC .*cron job 1 COMMAND completed", l).group(1) for l in excerpt if "cron job 1 COMMAND completed" in l]
r["steps"].append({
    "step": "fine-grained purge timing (1 s polling) - could not run",
    "command": "python fine_probe.py  (db.docs.insertOne({_id:'fine_probe', exp:<now-60s>}) then countDocuments every 1 s)",
    "at": "2026-11-25T20:12:13Z (first attempt), 2026-11-25T20:12:27Z (second attempt)", "ok": False,
    "response": {"code": 1, "codeName": "InternalError", "errmsg": "[ActivityId=ca8b5441-ea76-4910-a6aa-9f3a60b7acd9] An unexpected internal error has occurred.", "errorLabels": [],
                 "raisedDuring": "SCRAM-SHA-256 saslStart on connection open (pymongo OperationFailure)",
                 "gatewayLog": "gateway.auth:postgres.execute ... Error executing postgres request: Request failed with kind Pool, code InternalError, error_message_internal: Pool error due to generic postgres error: error connecting to server",
                 "postgresLog": ["2026-11-25 20:11:09.942 UTC [1556] PANIC:  could not write to file \"pg_wal/xlogtemp.1556\": No space left on device",
                                  "2026-11-25 20:11:09.949 UTC [97] DETAIL:  Failed process was running: SELECT * FROM documentdb_api.insert($1, $2, $3, NULL)  (backend 1556 was serving database t_query, not t_ttl)",
                                  "2026-11-25 20:11:10.030 UTC [1566] FATAL:  could not extend file \"base/5/19395\": No space left on device",
                                  "2026-11-25 20:11:10.032 UTC [97] LOG:  database system is shut down"],
                 "df_data": "/dev/vdb1 25G 24G 0 100% /data"},
    "reading": "The supplementary 1-second probe never ran: PostgreSQL inside the container had PANICked at 20:11:09 UTC (7 s after this test's polling ended at 20:11:02) on 'No space left on device' while another test's bulk insert into database t_query was running, so the gateway returns code 1 InternalError at authentication; the container was left as-is (not restarted) because it is shared.",
})
r["steps"].append({
    "step": "pg_cron TTL job timestamps from the PostgreSQL log (read-only, inside the container)",
    "command": "docker exec ddb-engine-test grep -n 'cron job 1 ' /data/pglog.log   (job 1 = CALL documentdb_api_internal.delete_expired_rows())",
    "at": "2026-11-25T20:13Z", "ok": True,
    "response": {"jobCommand": "CALL documentdb_api_internal.delete_expired_rows();", "starts_utc": cron_starts, "completed_utc": cron_done,
                 "ttlIndexCreatedAt_utc": "2026-11-25 20:07:00.128 (pglog: 'database t_ttl has collections: false' / 'Creating ... documents_25 for the sentinel database t_ttl')",
                 "excerptFile": os.path.join(HERE, "pglog_ttl_excerpt.txt")},
    "reading": "The purger is pg_cron job 1 firing once a minute at hh:mm:00 (+3 to +16 ms) and completing in 4 to 26 ms; every disappearance observed by the Mongo-side polling falls in the 15 s window that contains the next hh:mm:00 run.",
})
r["purgeCadence"] = {
    "observed": "Once per minute, at the top of the wall-clock minute (pg_cron '* * * * *'); each run completed in under 30 ms on this tiny collection.",
    "correlation": [
        {"doc": "past_date_60s (eligible at insert, inserted 20:07:00.129, 120 ms after the 20:07:00.006 run)", "purgedBy": "20:08:00.005 run", "lagAfterEligible_s": "~60 (missed the run that had just started)"},
        {"doc": "array_of_dates (one element 60 s past, one 1 day ahead)", "purgedBy": "20:08:00.005 run", "note": "array element compared individually: any expired Date element expires the document"},
        {"doc": "future_date_90s (eligible 20:08:35.129)", "purgedBy": "20:09:00.004 run", "lagAfterEligible_s": "~25"},
        {"doc": "probe2_past_date (inserted 20:08:02.189)", "purgedBy": "20:09:00.004 run", "lagAfterEligible_s": "~58"},
        {"doc": "probe3_past_date (inserted 20:09:02.235)", "purgedBy": "20:10:00.016 run", "lagAfterEligible_s": "~58"},
    ],
    "neverPurgedWithin4min": ["string_value (ISO string)", "number_value (epoch ms int)", "missing_field", "null_value"],
    "boundOnLag": "0 to ~60 s after eligibility on this build with an otherwise idle purger; the 'up to 60 s continuous batching' only matters when a single run cannot finish its batches.",
}
r["notes"] = ("Steps 1-10 ran 20:07:00-20:11:02 UTC and completed normally. At 20:11:09 UTC PostgreSQL in the shared container crashed on ENOSPC (/data 100% full) during another test's bulk insert (t_query / t_bulk_rerun backends); "
              "from then on every new connection fails at saslStart with code 1 InternalError. The container was not restarted or dropped by this test. "
              "Collection t_ttl.docs still holds string_value, number_value, missing_field, null_value (plus nothing else) as of the last successful poll. "
              "All observations are about documentdb-local (gateway buildInfo version 7.0.0, PostgreSQL 17 image ghcr.io/documentdb/documentdb/documentdb-local:latest pulled before 2026-11-25 20:02 UTC) and its default GUCs; they do not prove managed Azure DocumentDB cadence.")
json.dump(r, open(p, "w"), indent=2, default=str)
print(len(r["steps"]), cron_starts[-6:])
