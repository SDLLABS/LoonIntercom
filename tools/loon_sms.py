#!/usr/bin/env python3
"""LSMS1 one-time code generator for the indoor GSM access path.

Standard library only, so it runs unchanged in a-Shell (iOS), Termux
(Android) or any desktop Python 3. See protocol/sms-access.md.

  loon_sms.py init                 create a key + counter file (once per phone)
  loon_sms.py key                  print the key in hex for indoor provisioning
  loon_sms.py next [-r 1]          print "ABRIR 1 12345678" and advance counter
  loon_sms.py vector KEYHEX COUNTER RESOURCE [COMMAND]   test vector

The counter is advanced and written to disk BEFORE the code is printed, so a
crash or a lost SMS can never cause a code to be issued twice. The indoor
verifier accepts codes up to 20 counter values ahead, so unsent codes are
harmless as long as fewer than 20 are skipped in a row.
"""

import argparse
import hashlib
import hmac
import json
import os
import secrets
import sys

DOMAIN = b"LOON-SMS1"
DIGITS = 8
COMMANDS = {"ABRIR": 1}
DEFAULT_STATE = os.path.join(os.path.expanduser("~"), ".loon-sms.json")


def code(key: bytes, counter: int, resource: int, command: int = 1) -> str:
    if not 0 <= counter < 2**64 or not 1 <= resource <= 16:
        raise ValueError("counter or resource out of range")
    msg = DOMAIN + counter.to_bytes(8, "big") + bytes([resource, command])
    mac = hmac.new(key, msg, hashlib.sha256).digest()
    off = mac[31] & 0x0F
    value = int.from_bytes(mac[off:off + 4], "big") & 0x7FFFFFFF
    return str(value % 10**DIGITS).zfill(DIGITS)


def load(path):
    with open(path) as f:
        return json.load(f)


def save(path, state):
    tmp = path + ".tmp"
    fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w") as f:
        json.dump(state, f)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--state", default=DEFAULT_STATE, help="key/counter file")
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("init")
    sub.add_parser("key")
    n = sub.add_parser("next")
    n.add_argument("-r", "--resource", type=int, default=1)
    v = sub.add_parser("vector")
    v.add_argument("key_hex")
    v.add_argument("counter", type=int)
    v.add_argument("resource", type=int)
    v.add_argument("command", type=int, nargs="?", default=1)
    a = p.parse_args(argv)

    if a.cmd == "vector":
        print(code(bytes.fromhex(a.key_hex), a.counter, a.resource, a.command))
    elif a.cmd == "init":
        if os.path.exists(a.state):
            sys.exit(f"{a.state} already exists; refusing to overwrite a key")
        save(a.state, {"key": secrets.token_hex(32), "counter": 0})
        print(f"created {a.state}; provision this key indoors with 'key'")
    elif a.cmd == "key":
        print(load(a.state)["key"])
    elif a.cmd == "next":
        st = load(a.state)
        c = st["counter"]
        st["counter"] = c + 1
        save(a.state, st)  # advance first: never reuse a counter
        print(f"ABRIR {a.resource} {code(bytes.fromhex(st['key']), c, a.resource)}")


if __name__ == "__main__":
    main()
