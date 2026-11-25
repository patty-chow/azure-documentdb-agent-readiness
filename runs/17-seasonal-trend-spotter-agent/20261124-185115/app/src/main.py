"""
Example CLI that seeds (optional), runs the DocumentDB aggregation tool, calls the web-search tool, and combines signals into a ranked list.
"""
import os
import sys
import argparse
import json
# ensure src package imports work when running the script directly
sys.path.insert(0, os.path.dirname(__file__))
from tools.documentdb_tool import seasonal_sales_velocity
from tools.web_search_tool import fetch_trend_signals


def combine_signals(db_results, web_signals, weight_db=0.7, weight_web=0.3):
    # db_results: list of {category, season, total_quantity, total_value}
    # web_signals: list of {category, signal}

    # Aggregate DB signals per category across seasons (compute mean velocity)
    db_scores = {}
    for r in db_results:
        cat = r.get("category")
        qty = r.get("total_quantity", 0)
        db_scores.setdefault(cat, 0)
        db_scores[cat] += qty
    # normalize db scores
    if db_scores:
        max_db = max(db_scores.values())
    else:
        max_db = 1
    for k in db_scores:
        db_scores[k] = db_scores[k] / max_db

    web_map = {s["category"]: s for s in web_signals}

    categories = set(list(db_scores.keys()) + list(web_map.keys()))
    combined = []
    for c in categories:
        db_s = db_scores.get(c, 0)
        web_s = web_map.get(c, {}).get("signal", 0)
        score = weight_db * db_s + weight_web * web_s
        combined.append({"category": c, "db_score": db_s, "web_score": web_s, "combined_score": score, "web_evidence": web_map.get(c, {}).get("evidence")})
    combined.sort(key=lambda x: x["combined_score"], reverse=True)
    return combined


def run_example():
    print("Running seasonal aggregation against DocumentDB...")
    db_results = seasonal_sales_velocity(window_days=30, top_n=50)
    print(f"DB results: {len(db_results)} rows")
    # pick top categories from DB results
    top_categories = list({r['category'] for r in db_results})[:10]
    print("Top categories from DB:", top_categories)
    web_signals = fetch_trend_signals(top_categories)
    print("Web signals fetched for categories")

    combined = combine_signals(db_results, web_signals)
    print("Combined ranking:\n")
    print(json.dumps(combined, indent=2, default=str))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", action="store_true", help="Run the example agent flow")
    args = parser.parse_args()
    if args.run:
        run_example()
    else:
        print("Run with --run to execute the sample flow")
