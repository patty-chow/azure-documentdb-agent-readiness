"""Constructs a MongoClient with Python's DEFAULT warning filters and pings, so the parent
process can capture exactly what PyMongo prints to stderr on connect.

argv[1]: plain | global | target  (target = non-SRV mongodb:// to argv[2]:argv[3])
Reads credentials from the environment only; prints nothing secret.
"""
import os
import sys
import urllib.parse

from pymongo import MongoClient

which = sys.argv[1]
if which == "plain":
    client = MongoClient(os.environ["MANAGED_URI"], serverSelectionTimeoutMS=20000)
elif which == "global":
    client = MongoClient(os.environ["MANAGED_GLOBAL_URI"], serverSelectionTimeoutMS=20000)
else:
    uri = os.environ["MANAGED_URI"]
    user = urllib.parse.unquote(uri.split("://", 1)[1].split(":", 1)[0])
    client = MongoClient(
        host=sys.argv[2],
        port=int(sys.argv[3]),
        username=user,
        password=os.environ["MANAGED_PASS"],
        tls=True,
        authMechanism="SCRAM-SHA-256",
        retryWrites=False,
        serverSelectionTimeoutMS=20000,
    )
print("constructed", flush=True)
print("ping:", client.admin.command("ping"), flush=True)
client.close()
print("closed", flush=True)
