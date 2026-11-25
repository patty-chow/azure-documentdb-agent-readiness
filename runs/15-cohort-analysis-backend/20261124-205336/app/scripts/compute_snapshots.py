from app.cohorts import compute_and_store_snapshot

if __name__ == '__main__':
    snap = compute_and_store_snapshot(months_back=12)
    print('Created snapshot:', snap.get('snapshot_name'))
    print('Buckets:', len(snap.get('buckets', [])))
