import os
import json
import statistics
from typing import List, Dict, Any

from .db import get_db
from .tools import run_aggregation_and_index


class LocalSummarizer:
    """Simple local summarizer used when no external LLM key is provided."""

    @staticmethod
    def summarize(agg: List[Dict[str, Any]], wallet: str) -> str:
        if not agg:
            return f"No transactions found for wallet {wallet}."
        totals = [d["total"] for d in agg]
        counts = [d["count"] for d in agg]
        mean_vol = statistics.mean(totals)
        mean_count = statistics.mean(counts)
        stdev_vol = statistics.pstdev(totals) if len(totals) > 1 else 0
        stdev_count = statistics.pstdev(counts) if len(counts) > 1 else 0

        anomalies = []
        for d in agg:
            vol_z = (d["total"] - mean_vol) / stdev_vol if stdev_vol > 0 else 0
            cnt_z = (d["count"] - mean_count) / stdev_count if stdev_count > 0 else 0
            if abs(vol_z) >= 3 or abs(cnt_z) >= 3:
                anomalies.append({"date": d["date"], "total": d["total"], "count": d["count"], "vol_z": vol_z, "cnt_z": cnt_z})

        lines = [f"Summary for wallet {wallet}:" , f"- Observed {len(agg)} days; mean daily volume ${mean_vol:.2f}, mean daily tx count {mean_count:.1f}."]
        if anomalies:
            lines.append("- Anomalies detected on these dates:")
            for a in anomalies:
                lines.append(f"  * {a['date']}: total=${a['total']:.2f}, count={a['count']} (vol_z={a['vol_z']:.2f}, cnt_z={a['cnt_z']:.2f})")
        else:
            lines.append("- No statistical outliers detected (z-score threshold 3.0).")
        return "\n".join(lines)


class DummyLLM:
    def __call__(self, prompt: str) -> str:
        marker = "AGG_JSON:\n"
        if marker in prompt:
            try:
                j = prompt.split(marker,1)[1].strip()
                data = json.loads(j)
                return LocalSummarizer.summarize(data.get("agg", []), data.get("wallet","<wallet>"))
            except Exception:
                return "Failed to parse aggregation JSON for local summarizer."
        return "No aggregation data provided."


def analyze_wallet(wallet_address: str) -> str:
    db = get_db()
    agg = run_aggregation_and_index(db, wallet_address)

    # Try to use OpenAI via LangChain/OpenAI if API key is present
    openai_key = os.environ.get("OPENAI_API_KEY")
    if openai_key:
        try:
            # Use OpenAI API directly for a simple prompt-completion
            import openai
            openai.api_key = openai_key
            prompt = f"Please summarize the following wallet activity and list anomalies:\nAGG_JSON:\n{json.dumps({'wallet': wallet_address, 'agg': agg})}"
            resp = openai.ChatCompletion.create(model="gpt-3.5-turbo", messages=[{"role":"user","content":prompt}], max_tokens=500)
            summary = resp["choices"][0]["message"]["content"].strip()
        except Exception as e:
            summary = LocalSummarizer.summarize(agg, wallet_address) + f"\n\n(Note: OpenAI summarization failed: {e})"
    else:
        # offline summarizer
        llm = DummyLLM()
        prompt = f"Summarize:\nAGG_JSON:\n{json.dumps({'wallet': wallet_address, 'agg': agg})}"
        summary = llm(prompt)
    return summary
