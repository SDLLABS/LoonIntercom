"""Build the Klingelbox explorer into one self-contained HTML file.

    python build.py            -> dist/klingelbox-explorer.html

Inputs (all in this folder):
    skeleton.json  structure: zones, layers, nodes, edges, tours, solder jobs, open points
    layout.json    canvas coordinates, short type tags, wire route overrides
    texts.json     optional EN/DE copy per node, edge, tour and solder job;
                   anything missing falls back to the skeleton's names and hints
    template.html  page, styles and the rendering engine

The build refuses to write if a reference is broken, so a typo in an id shows
up here and not as a silently missing wire on the page.
"""
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
OUT = HERE / "dist" / "klingelbox-explorer.html"


def load(name, required=True):
    p = HERE / name
    if not p.exists():
        if required:
            sys.exit(f"missing {name}")
        return {}
    return json.loads(p.read_text(encoding="utf-8"))


def check(sk, ly, tx):
    errors = []
    node_ids = {n["id"] for n in sk["nodes"]}
    layer_ids = {l["id"] for l in sk["layers"]}
    zone_ids = {z["id"] for z in sk["zones"]}
    edge_ids = {e["id"] for e in sk["edges"]}
    for n in sk["nodes"]:
        if n["zone"] not in zone_ids:
            errors.append(f"node {n['id']}: unknown zone {n['zone']}")
        if n["id"] not in ly["nodes"]:
            errors.append(f"node {n['id']}: no position in layout.json")
    for nid in ly["nodes"]:
        if nid not in node_ids:
            errors.append(f"layout.json places unknown node {nid}")
    for e in sk["edges"]:
        for end in ("from", "to"):
            if e[end] not in node_ids:
                errors.append(f"edge {e['id']}: unknown {end} {e[end]}")
        if e["layer"] not in layer_ids:
            errors.append(f"edge {e['id']}: unknown layer {e['layer']}")
    for rid in ly.get("routes", {}):
        if rid not in edge_ids:
            errors.append(f"layout.json routes unknown edge {rid}")
    for t in sk["tours"]:
        for i, st in enumerate(t["steps"]):
            for n in st["nodes"]:
                if n not in node_ids:
                    errors.append(f"tour {t['id']} step {i+1}: unknown node {n}")
            for e in st["edges"]:
                if e not in edge_ids:
                    errors.append(f"tour {t['id']} step {i+1}: unknown edge {e}")
    for s in sk["solder"]:
        if s["node"] not in node_ids:
            errors.append(f"solder job for unknown node {s['node']}")
    for kind, ids in (("nodes", node_ids), ("edges", edge_ids),
                      ("tours", {t["id"] for t in sk["tours"]}),
                      ("solder", {s["node"] for s in sk["solder"]})):
        for k in tx.get(kind, {}):
            if k not in ids:
                errors.append(f"texts.json {kind}: unknown id {k}")
    for kind in ("nodes", "edges", "tours", "solder"):
        for k, v in tx.get(kind, {}).items():
            for lang in ("en", "de"):
                if lang not in v:
                    errors.append(f"texts.json {kind} {k}: no {lang}")
    for t in sk["tours"]:
        tt = tx.get("tours", {}).get(t["id"])
        if tt:
            for lang in ("en", "de"):
                if len(tt[lang].get("steps", [])) != len(t["steps"]):
                    errors.append(f"texts.json tour {t['id']} {lang}: step count differs")
    errors += check_roadmap(sk, ly, tx, node_ids)
    return errors


TASK_STATES = {"done", "doing", "open", "waiting", "decide"}


def check_roadmap(sk, ly, tx, node_ids):
    errors = []
    ms = sk.get("milestones", [])
    ids = [m["id"] for m in ms]
    if len(ids) != len(set(ids)):
        errors.append("milestones: duplicate id")
    cards = ly.get("roadmap", {}).get("cards", {})
    for m in ms:
        for ref in m.get("needs", []) + m.get("soft", []):
            if ref not in ids:
                errors.append(f"milestone {m['id']}: needs unknown milestone {ref}")
        if m["id"] not in cards:
            errors.append(f"milestone {m['id']}: no card in layout.json roadmap")
        mt = tx.get("milestones", {}).get(m["id"])
        for k in m["tasks"]:
            if k["status"] not in TASK_STATES:
                errors.append(f"milestone {m['id']} task {k['id']}: unknown status {k['status']}")
            if k.get("node") and k["node"] not in node_ids:
                errors.append(f"milestone {m['id']} task {k['id']}: unknown node {k['node']}")
            for lang in ("en", "de"):
                if mt and k["id"] not in mt.get(lang, {}).get("tasks", {}):
                    errors.append(f"texts.json milestone {m['id']} {lang}: no text for task {k['id']}")
    for link in ly.get("roadmap", {}).get("links", []):
        for end in ("from", "to"):
            if link[end] not in ids:
                errors.append(f"layout.json roadmap link: unknown milestone {link[end]}")
    return errors


def roadmap_markdown(sk, tx):
    """The roadmap as plain Markdown (English), for readers on GitHub."""
    ms = sk.get("milestones", [])
    if not ms:
        return None
    no = {m["id"]: f"M{i}" for i, m in enumerate(ms)}
    title = {m["id"]: tx["milestones"][m["id"]]["en"]["title"] for m in ms}
    status = {"done": "done", "now": "now", "next": "next", "later": "later"}
    mark = {"done": "[x]", "doing": "[~]", "open": "[ ]", "waiting": "[ ] (waiting)", "decide": "[ ] ◆"}
    out = ["# Roadmap", "",
           f"State: {sk.get('state', '')}. Generated from `explorer/skeleton.json` and `explorer/texts.json`;",
           "the interactive version is the roadmap section of the [explorer](../explorer/).", "",
           "`[x]` done · `[~]` under way · `[ ]` to do · `◆` a decision that must be locked in", ""]
    locks = [(m, k) for m in ms for k in m["tasks"] if k["status"] == "decide"]
    if locks:
        out += ["## Must-lock-ins", ""]
        for m, k in locks:
            out.append(f"- ◆ {tx['milestones'][m['id']]['en']['tasks'][k['id']]} ({no[m['id']]})")
        out.append("")
    for m in ms:
        t = tx["milestones"][m["id"]]["en"]
        done = sum(1 for k in m["tasks"] if k["status"] == "done")
        out += [f"## {no[m['id']]} · {t['title']}", "",
                f"**{status[m['status']].capitalize()}** · {done} of {len(m['tasks'])} tasks done", "", t["why"], ""]
        needs = [f"{no[r]} {title[r]}" for r in m.get("needs", [])]
        soft = [f"{no[r]} {title[r]} (bracket and dummy plate)" for r in m.get("soft", [])]
        if needs or soft:
            out += ["Needs: " + ", ".join(needs + soft), ""]
        for k in m["tasks"]:
            out.append(f"- {mark[k['status']]} {t['tasks'][k['id']]}")
        out += ["", f"*Done when:* {t['done_when']}", ""]
    return "\n".join(out)


def main():
    sk = load("skeleton.json")
    ly = load("layout.json")
    tx = load("texts.json", required=False)
    errors = check(sk, ly, tx)
    if errors:
        print("\n".join(errors))
        sys.exit(f"{len(errors)} problem(s), nothing written")
    missing = {
        kind: sorted(set(ids) - set(tx.get(kind, {})))
        for kind, ids in (("nodes", [n["id"] for n in sk["nodes"]]),
                          ("edges", [e["id"] for e in sk["edges"]]),
                          ("tours", [t["id"] for t in sk["tours"]]),
                          ("solder", [s["node"] for s in sk["solder"]]))
    }
    data = {"skeleton": sk, "layout": ly, "texts": tx, "state": sk.get("state", "")}
    blob = json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    html = (HERE / "template.html").read_text(encoding="utf-8")
    if "__KB_DATA__" not in html:
        sys.exit("template.html has no __KB_DATA__ placeholder")
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(html.replace("__KB_DATA__", blob), encoding="utf-8")
    print(f"wrote {OUT.relative_to(HERE)} ({OUT.stat().st_size // 1024} KB)")
    md = roadmap_markdown(sk, tx)
    if md:
        (OUT.parent / "roadmap.md").write_text(md, encoding="utf-8")
        print("wrote dist/roadmap.md")
    for kind, ids in missing.items():
        if ids:
            print(f"  no text yet for {len(ids)} {kind}: {', '.join(ids)}")


if __name__ == "__main__":
    main()
