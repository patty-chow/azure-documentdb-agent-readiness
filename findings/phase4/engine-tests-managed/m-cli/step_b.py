"""Step (b): first-use dynamic extension install of `az documentdb` in a brand-new AZURE_CONFIG_DIR.

Run: python -I step_b.py <phase>
  notty   mktemp -d config dir; `az documentdb mongocluster list` with stdin from /dev/null (no TTY);
          inventory of what landed in the dir; a second identical run; then the dir is removed
  tty     contrast: a second fresh dir, the same command on a pseudo-terminal, answering "n" to any
          install prompt (so nothing is installed); then the dir is removed

The temporary config dirs are created under the scratchpad root (not in this scripts folder) and
AZURE_EXTENSION_DIR is removed from the child environment so the user's installed extensions
cannot be found.
"""
import json
import os
import pty
import select
import shutil
import subprocess
import sys
import time

TEST_DIR = "/private/tmp/claude-501/-Users-julietai-claude/40f65f7c-640c-44c6-8eab-a8434709e1ff/scratchpad/managed-tests/m-cli"
sys.path.insert(0, TEST_DIR)
import common  # noqa: E402

SCRATCH = "/private/tmp/claude-501/-Users-julietai-claude/40f65f7c-640c-44c6-8eab-a8434709e1ff/scratchpad"
CMD = ["az", "documentdb", "mongocluster", "list"]


def fresh_dir(step_id, prefix):
    rec, out, err, code = common.run(step_id, ["mktemp", "-d", os.path.join(SCRATCH, prefix + ".XXXXXX")])
    d = out.strip()
    assert code == 0 and d.startswith(SCRATCH) and os.path.isdir(d), (code, d)
    common.record(step_id + "-contents", kind="derived", command=f"os.listdir({d!r})", entries=sorted(os.listdir(d)))
    return d


def child_env(cfg):
    env = dict(os.environ)
    had = {k: True for k in ("AZURE_EXTENSION_DIR", "AZURE_CONFIG_DIR") if k in env}
    env.pop("AZURE_EXTENSION_DIR", None)
    env["AZURE_CONFIG_DIR"] = cfg
    return env, had


def inventory(step_id, cfg):
    tree = []
    for root, dirs, files in os.walk(cfg):
        rel = os.path.relpath(root, cfg)
        depth = 0 if rel == "." else rel.count(os.sep) + 1
        if depth > 2:
            dirs[:] = []
            continue
        for f in sorted(files):
            p = os.path.join(root, f)
            tree.append({"path": os.path.normpath(os.path.join(rel, f)), "bytes": os.path.getsize(p)})
        for dname in sorted(dirs):
            tree.append({"path": os.path.normpath(os.path.join(rel, dname)) + "/"})
    common.record(step_id, kind="derived", command=f"walk of $AZURE_CONFIG_DIR to depth 2 ({cfg})", entries=tree)
    return tree


def remove(step_id, cfg):
    """Remove the temp dir. az starts a background telemetry uploader after each command that writes
    logs/telemetry.log into $AZURE_CONFIG_DIR, so wait for it first and remove again if it reappears."""
    assert cfg.startswith(SCRATCH + "/azcfg-m-cli")
    time.sleep(15)
    shutil.rmtree(cfg, ignore_errors=True)
    passes = 1
    time.sleep(20)
    if os.path.exists(cfg):
        shutil.rmtree(cfg, ignore_errors=True)
        passes += 1
        time.sleep(10)
    common.record(step_id, kind="derived",
                  command=f"sleep 15; shutil.rmtree({cfg!r}); sleep 20; remove again if the telemetry uploader recreated it; os.path.exists",
                  removal_passes=passes, exists_after=os.path.exists(cfg))


phase = sys.argv[1]

if phase == "notty":
    cfg = fresh_dir("b1-mktemp", "azcfg-m-cli")
    env, had = child_env(cfg)
    common.record("b1b-env", kind="derived", command="environment of the child az process",
                  AZURE_CONFIG_DIR=cfg, AZURE_EXTENSION_DIR_in_parent=had.get("AZURE_EXTENSION_DIR", False),
                  AZURE_EXTENSION_DIR_in_child=False, stdin="/dev/null", stdout="pipe", stderr="pipe")
    disp = f"AZURE_CONFIG_DIR={cfg} az documentdb mongocluster list < /dev/null"
    rec, out, err, code = common.run("b2-first-run-no-tty", CMD, display=disp, env=env, timeout=580)
    print(json.dumps({"exit": code, "dur": rec["duration_s"], "stdout": common.mask(out)[:3000], "stderr": common.mask(err)[:6000]}, indent=1))
    inventory("b3-config-dir-after-first-run", cfg)
    rec2, out2, err2, code2 = common.run("b4-extension-list-in-temp-dir",
                                         ["az", "extension", "list", "--query",
                                          "[].{name:name, version:version, preview:preview, path:path}", "-o", "json"],
                                         display=f"AZURE_CONFIG_DIR={cfg} az extension list --query \"[].{{name:name, version:version, preview:preview, path:path}}\" -o json < /dev/null",
                                         env=env, parse_json=True)
    print(json.dumps({"ext_list_exit": code2, "json": rec2.get("stdout_json"), "stderr": common.mask(err2)[:1500]}, indent=1))
    rec3, out3, err3, code3 = common.run("b5-second-run-no-tty", CMD, display=disp, env=env, timeout=580)
    print(json.dumps({"second_exit": code3, "dur": rec3["duration_s"], "stdout": common.mask(out3)[:2000], "stderr": common.mask(err3)[:3000]}, indent=1))
    remove("b6-remove-temp-dir", cfg)

elif phase == "tty":
    cfg = fresh_dir("b7-mktemp-tty", "azcfg-m-cli-tty")
    env, had = child_env(cfg)
    t0 = time.time()
    started = common.now_iso()
    pid, fd = pty.fork()
    if pid == 0:  # child: stdin, stdout and stderr are the pty slave
        os.execvpe("az", CMD, env)
    buf = b""
    answered = None
    deadline = time.time() + 240
    status = None
    while time.time() < deadline:
        r, _, _ = select.select([fd], [], [], 1.0)
        if fd in r:
            try:
                chunk = os.read(fd, 4096)
            except OSError:
                chunk = b""
            if not chunk:
                break
            buf += chunk
            if answered is None and b"(Y/n)" in buf:
                os.write(fd, b"n\n")
                answered = {"answer": "n", "after_s": round(time.time() - t0, 2)}
        wpid, st = os.waitpid(pid, os.WNOHANG)
        if wpid == pid:
            status = st
            # drain
            try:
                while True:
                    r, _, _ = select.select([fd], [], [], 0.5)
                    if fd not in r:
                        break
                    chunk = os.read(fd, 4096)
                    if not chunk:
                        break
                    buf += chunk
            except OSError:
                pass
            break
    timed_out = False
    if status is None:
        # The loop also ends on pty EOF (the child closed the terminal by exiting): reap it before
        # treating the run as a timeout. (Fixed after the 2026-11-25 run, which recorded
        # timed_out=true on EOF; see step b8b.)
        for _ in range(50):
            wpid, st = os.waitpid(pid, os.WNOHANG)
            if wpid == pid:
                status = st
                break
            time.sleep(0.1)
    if status is None:
        try:
            os.kill(pid, 9)
        except ProcessLookupError:
            pass
        _, status = os.waitpid(pid, 0)
        timed_out = True
    code = os.waitstatus_to_exitcode(status)
    text = buf.decode("utf-8", "replace")
    common.record("b8-first-run-pty", kind="pty",
                  command=f"AZURE_CONFIG_DIR={cfg} az documentdb mongocluster list   (stdin/stdout/stderr on a pseudo-terminal; "
                          f"the script types 'n' + Enter when '(Y/n)' appears)",
                  started_at=started, duration_s=round(time.time() - t0, 2), exit_code=code, timed_out=timed_out,
                  answered=answered, pty_output=text)
    print(json.dumps(common.mask({"exit": code, "timed_out": timed_out, "answered": answered, "output": text[:5000]}), indent=1))
    inventory("b9-config-dir-after-pty-run", cfg)
    remove("b10-remove-temp-dir-tty", cfg)
else:
    raise SystemExit(f"unknown phase {phase}")
