import argparse
from sample_retail_09.agents import Orchestrator


def main(all_items=False, item_id=None):
    orch = Orchestrator()
    if all_items:
        res = orch.run_for_all()
        print(f"Created {len(res)} purchase orders")
        for r in res:
            print(r)
    elif item_id:
        po = orch.create_purchase_order(item_id)
        if po:
            print("Created PO:", po)
        else:
            print("No PO created (no supplier or already ordered)")
    else:
        print("Provide --all or --item ITEM_ID")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--all", action="store_true")
    p.add_argument("--item", dest="item_id")
    args = p.parse_args()
    main(all_items=args.all, item_id=args.item_id)
