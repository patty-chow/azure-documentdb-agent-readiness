import os
import uuid
import json
from datetime import datetime
from typing import Dict, Any, List
from pymongo import ASCENDING
from .db import get_db

class DataExtractionAgent:
    def __init__(self, db):
        self.db = db

    def extract(self, reporting_period: str) -> Dict[str, Any]:
        # Query transactions and accounts for the reporting period
        tx_coll = self.db.transactions
        acc_coll = self.db.accounts

        tx_cursor = tx_coll.find({"reporting_period": reporting_period})
        transactions = list(tx_cursor)

        # Find related accounts
        account_ids = list({tx['account_id'] for tx in transactions})
        accounts = list(acc_coll.find({"_id": {"$in": account_ids}}))

        return {"transactions": transactions, "accounts": accounts}

class ValidationAgent:
    def __init__(self):
        pass

    def validate(self, extracted: Dict[str, Any]) -> Dict[str, Any]:
        # Simple rules: every transaction must reference an existing account
        accounts = {a['_id'] for a in extracted.get('accounts', [])}
        transactions = extracted.get('transactions', [])
        issues = []
        for tx in transactions:
            if tx.get('account_id') not in accounts:
                issues.append({"tx_id": tx.get('_id'), "issue": "missing_account"})
        # rule: reporting must have at least one transaction
        if len(transactions) == 0:
            issues.append({"issue": "no_transactions"})

        status = 'pass' if len(issues) == 0 else 'fail'
        return {"status": status, "issues": issues}

class FilingAgent:
    def __init__(self, db):
        self.db = db

    def format_and_save(self, reporting_period: str, extracted: Dict[str, Any], validation: Dict[str, Any], run_id: str) -> str:
        # Simple regulatory JSON: header + accounts + transactions + validation
        filing = {
            "reporting_period": reporting_period,
            "generated_at": datetime.utcnow().isoformat() + 'Z',
            "accounts": [{"_id": a['_id'], "name": a.get('name'), "region": a.get('region')} for a in extracted.get('accounts', [])],
            "transactions": [{"_id": t['_id'], "account_id": t.get('account_id'), "date": t.get('date'), "amount": t.get('amount'), "currency": t.get('currency')} for t in extracted.get('transactions', [])],
            "validation": validation,
            "run_id": run_id
        }
        # Save to examples/ and also annotate workflow_runs
        os.makedirs('examples', exist_ok=True)
        out_path = f"examples/filing_{run_id}.json"
        with open(out_path, 'w', encoding='utf8') as f:
            json.dump(filing, f, default=str, indent=2)
        return out_path

class Orchestrator:
    def __init__(self, db):
        self.db = db
        self.data_agent = DataExtractionAgent(db)
        self.validation_agent = ValidationAgent()
        self.filing_agent = FilingAgent(db)

    def _ensure_indexes(self):
        # Create helpful indexes (idempotent)
        self.db.transactions.create_index([('reporting_period', ASCENDING), ('date', ASCENDING)], name='idx_period_date')
        self.db.transactions.create_index([('account_id', ASCENDING)], name='idx_account')
        self.db.workflow_runs.create_index([('run_id', ASCENDING)], unique=True, name='idx_run_id')
        self.db.workflow_runs.create_index([('start_ts', ASCENDING)], name='idx_start_ts')

    def _log_step(self, run_doc_id, step_name, status, msg=None):
        step = {"name": step_name, "status": status, "timestamp": datetime.utcnow(), "msg": msg}
        self.db.workflow_runs.update_one({'_id': run_doc_id}, {'$push': {'steps': step}, '$set': {'end_ts': None}}, upsert=False)

    def run(self, reporting_period: str) -> Dict[str, Any]:
        # Create a workflow_runs document
        run_id = str(uuid.uuid4())
        run_doc = {
            'run_id': run_id,
            'start_ts': datetime.utcnow(),
            'reporting_period': reporting_period,
            'steps': []
        }
        res = self.db.workflow_runs.insert_one(run_doc)
        run_doc_id = res.inserted_id

        try:
            self._ensure_indexes()
            # Step 1: extract
            self.data_agent.extract  # no-op to show function exists
            self._log_step(run_doc_id, 'extract:start', 'running')
            extracted = self.data_agent.extract(reporting_period)
            self._log_step(run_doc_id, 'extract:finish', 'success', f"extracted {len(extracted.get('transactions', []))} transactions")

            # Step 2: validate
            self._log_step(run_doc_id, 'validate:start', 'running')
            validation = self.validation_agent.validate(extracted)
            self._log_step(run_doc_id, 'validate:finish', 'success' if validation.get('status') == 'pass' else 'fail', f"{len(validation.get('issues', []))} issues")

            # Step 3: filing/format
            self._log_step(run_doc_id, 'filing:start', 'running')
            out_path = self.filing_agent.format_and_save(reporting_period, extracted, validation, run_id)
            self._log_step(run_doc_id, 'filing:finish', 'success', f"wrote {out_path}")

            # mark end
            self.db.workflow_runs.update_one({'_id': run_doc_id}, {'$set': {'end_ts': datetime.utcnow()}})

            return {"run_id": run_id, "out_path": out_path, "validation": validation}
        except Exception as e:
            self._log_step(run_doc_id, 'orchestrator:error', 'error', str(e))
            self.db.workflow_runs.update_one({'_id': run_doc_id}, {'$set': {'end_ts': datetime.utcnow()}})
            raise
