import os
import mongomock
import pytest
from unittest.mock import patch

os.environ.setdefault('DOCUMENTDB_URI', 'mongodb://localhost:27017')

@patch('src.db.MongoClient')
def test_seed_upserts(mock_mongo_client):
    # Use mongomock for the DB
    client = mongomock.MongoClient()
    mock_mongo_client.return_value = client

    # import seed module and run main
    import seed
    # Run seeding (should not raise)
    seed.main()

    db = client['sample_healthcare_13']
    coll = db['high_risk_profiles']
    assert coll.count_documents({}) == int(os.environ.get('SEED_COUNT', '200'))

