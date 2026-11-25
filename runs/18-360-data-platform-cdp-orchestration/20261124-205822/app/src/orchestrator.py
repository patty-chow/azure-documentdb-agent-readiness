import time
import uuid
from .db import get_db
from .agents import IngestAgent, DedupAgent, EnrichAgent

class Orchestrator:
    def __init__(self):
        self.db = get_db()
        self.ingest = IngestAgent()
        self.dedup = DedupAgent()
        self.enrich = EnrichAgent()

    def run_batch(self, incoming_records=None):
        run_id = str(uuid.uuid4())
        workflows = self.db['workflows']
        start = time.time()
        workflows.insert_one({'run_id': run_id, 'stage': 'started', 'start_time': start})
        try:
            if incoming_records:
                self.ingest.ingest(incoming_records)
                workflows.insert_one({'run_id': run_id, 'stage': 'ingest_completed', 'time': time.time()})

            self.dedup.run_merging_pass()
            workflows.insert_one({'run_id': run_id, 'stage': 'dedupe_completed', 'time': time.time()})

            self.enrich.run_enrichment_pass()
            workflows.insert_one({'run_id': run_id, 'stage': 'enrich_completed', 'time': time.time()})

            end = time.time()
            workflows.insert_one({'run_id': run_id, 'stage': 'finished', 'end_time': end, 'duration_sec': end - start})
            return run_id
        except Exception as e:
            workflows.insert_one({'run_id': run_id, 'stage': 'failed', 'error': str(e)})
            raise
