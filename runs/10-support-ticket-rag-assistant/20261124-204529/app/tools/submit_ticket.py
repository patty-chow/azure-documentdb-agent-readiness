import sys
import requests
import json

if len(sys.argv) < 2:
    print("Usage: submit_ticket.py 'ticket text'")
    sys.exit(1)

ticket = sys.argv[1]
resp = requests.post('http://127.0.0.1:5000/suggest', json={'ticket_text': ticket})
print(resp.status_code)
print(resp.text)
