"""Run oidc_node.mjs and store a masked copy of its output. Run with the project venv python -I."""
import json
import os
import sys

TEST_DIR = "/private/tmp/claude-501/-Users-julietai-claude/40f65f7c-640c-44c6-8eab-a8434709e1ff/scratchpad/managed-tests/m-entra"
sys.path.insert(0, TEST_DIR)
import common  # noqa: E402

node_dir = os.path.join(TEST_DIR, "node")
unmasked = os.path.join(common.RAW_DIR, ".oidc_node_unmasked.json")
env = dict(os.environ, M_PLAIN_HOST=common.ENV["MANAGED_HOST"], M_GLOBAL_HOST=common.ENV["MANAGED_GLOBAL_HOST"])
rec, out, err, code = common.run("f1-node-oidc", ["node", os.path.join(TEST_DIR, "oidc_node.mjs"), node_dir, unmasked],
                                 display="node oidc_node.mjs <test-dir>/node <unmasked-out>  (env M_PLAIN_HOST, M_GLOBAL_HOST)",
                                 env=env, cwd=TEST_DIR, timeout=590)
data = json.load(open(unmasked))
os.remove(unmasked)
with open(os.path.join(common.RAW_DIR, "oidc_node.json"), "w") as fh:
    json.dump(common.mask(data), fh, indent=1)
print(rec["stdout"])
print("stderr:", (rec["stderr"] or "")[:2000])
print("exit:", code)
