import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.main import get_branch_metrics, refresh_summaries, ask

print('Calling get_branch_metrics(BR-001)')
try:
    resp = get_branch_metrics('BR-001')
    print('OK, keys:', list(resp.keys()))
except Exception as e:
    print('get_branch_metrics failed:', e)

print('Calling refresh_summaries()')
try:
    resp2 = refresh_summaries()
    print('refresh_summaries returned:', resp2)
except Exception as e:
    print('refresh_summaries failed:', e)

print('Calling ask(...)')
try:
    class R: pass
    r = R()
    r.query = 'total transactions'
    resp3 = ask(r)
    print('ask returned:', resp3)
except Exception as e:
    print('ask failed:', e)
