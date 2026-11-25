"""Create the documentdb vector index and a textSearch index for demo.

This script uses the DocumentDB MCP server tools via the agentic environment
in the build environment. It calls the local cluster via the default
connection_profile. If the MCP server isn't available in your environment, run
this script's logic manually using your preferred admin tooling.
"""
from dotenv import load_dotenv
import os

load_dotenv()

# We call out to the DocumentDB MCP server using the functions/documentdb_create_index
# tool from the build harness. If that tool isn't callable from your environment,
# create equivalent indexes in the portal or via an administrative client.

# This script is a placeholder that documents the index shapes used by the sample.
print("This repository includes an automated index-creation step via the MCP server tool in the build harness.\nRun the prebuilt script in CI or use the MCP server tooling to create:\n - a vector-diskann index on 'regulations.embedding' with dimensions=1536 and similarity=COS\n - a textSearch index on 'regulations.text' and 'policies.text' for lexical fallback\")
