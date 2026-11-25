from datetime import datetime, timedelta
from pymongo import ASCENDING, DESCENDING
from .db import get_db
import uuid

DB = get_db()

class ForecastAgent:
    """Reads recent sales_velocity docs and predicts a reorder quantity.
    Simple heuristic: avg daily sales over last N days * (lead_time_days + safety_days) - current_stock_estimate
    For demo we don't track stock; return a conservative reorder.
    """
    def __init__(self, lookback_days=14, safety_days=3):
        self.lookback_days = lookback_days
        self.safety_days = safety_days

    def predict_reorder_qty(self, item_id, lead_time_days=7):
        coll = DB["sales_velocity"]
        cutoff = datetime.utcnow() - timedelta(days=self.lookback_days)
        cursor = coll.find({"item_id": item_id, "date": {"$gte": cutoff}})
        counts = [d.get("sales_count", 0) for d in cursor]
        if not counts:
            # No history → minimal reorder
            return 10
        avg_daily = sum(counts) / max(len(counts), 1)
        days_covered = lead_time_days + self.safety_days
        qty = int(max(1, round(avg_daily * days_covered)))
        return qty


class SupplierAgent:
    """Selects the best supplier for an item based on lead_times collection (lowest lead_time_days)."""
    def select_supplier(self, item_id):
        coll = DB["lead_times"]
        doc = coll.find_one({"item_id": item_id}, sort=[("lead_time_days", ASCENDING)])
        return doc


class Orchestrator:
    def __init__(self):
        self.forecast_agent = ForecastAgent()
        self.supplier_agent = SupplierAgent()
        self.po_coll = DB["purchase_orders"]
        self.mem_coll = DB["agent_memory"]

    def _already_ordered(self, item_id):
        # Check agent_memory for an open PO marker for this run
        doc = self.mem_coll.find_one({"item_id": item_id, "status": "ordered"})
        return doc is not None

    def _mark_ordered(self, item_id, po_id):
        self.mem_coll.update_one({"item_id": item_id}, {"$set": {"item_id": item_id, "po_id": po_id, "status": "ordered", "created_at": datetime.utcnow()}}, upsert=True)

    def create_purchase_order(self, item_id):
        if self._already_ordered(item_id):
            return None
        supplier = self.supplier_agent.select_supplier(item_id)
        if not supplier:
            # No supplier known
            return None
        lead = supplier.get("lead_time_days", 7)
        qty = self.forecast_agent.predict_reorder_qty(item_id, lead_time_days=lead)
        po = {
            "po_id": str(uuid.uuid4()),
            "item_id": item_id,
            "supplier_id": supplier.get("supplier_id"),
            "qty": qty,
            "created_at": datetime.utcnow(),
            "status": "created",
            "schemaVersion": 1,
        }
        self.po_coll.insert_one(po)
        self._mark_ordered(item_id, po["po_id"])
        return po

    def run_for_all(self, limit=50):
        # pick distinct item_ids from sales_velocity or lead_times
        item_ids = set()
        for coll_name in ("lead_times", "sales_velocity"):
            cursor = DB[coll_name].distinct("item_id")
            for id in cursor:
                item_ids.add(id)
        results = []
        for item in list(item_ids)[:limit]:
            po = self.create_purchase_order(item)
            if po:
                results.append(po)
        return results
