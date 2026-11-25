import sys
import asyncio
sys.path.insert(0, '.')
from src.db import get_client, init_db

async def run():
    await init_db()
    client = await get_client()
    pipeline = [
        {'$match': {'patientId':'patient_001','testCode':'GLU'}},
        {'$setWindowFields':{
            'partitionBy': {'patientId':'$patientId','testCode':'$testCode'},
            'sortBy': {'timestamp':1},
            'output': {'movingAvg': {'$avg':'$value','window': {'documents': [-4,0]}}}
        }},
        {'$project': {'_id':0,'patientId':1,'testCode':1,'timestamp':1,'value':1,'movingAvg':1}}
    ]
    cursor = client['sample_healthcare_07']['lab_results'].aggregate(pipeline)
    results = [r async for r in cursor]
    print('Results count:', len(results))
    for r in results[:5]:
        print(r)

if __name__ == '__main__':
    asyncio.run(run())
