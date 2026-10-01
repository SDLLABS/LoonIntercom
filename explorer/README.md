# Explorer

An interactive map of the whole system: every part, every wire type as a switchable layer,
every joint and solder spot, and step-by-step walkthroughs (a ring, the power path, winter,
the light, a call). English and German, light and dark, works on a phone.

**Open it:** download [`dist/klingelbox-explorer.html`](dist/klingelbox-explorer.html) and open
it in a browser. It is one self-contained file; the only outside request is for web fonts.

## How it is built

| File | Role |
|---|---|
| `skeleton.json` | the structure and the single source of truth: zones, wire layers, parts (with status), connections, walkthroughs, solder jobs, open points |
| `layout.json` | where each part sits on the 1600 × 1000 canvas, short type tags, and route hints for wires that need them |
| `texts.json` | the English and German copy for every part, wire, walkthrough and solder job |
| `template.html` | page, styles and the rendering engine (plain JavaScript, no libraries) |
| `build.py` | merges the four into `dist/klingelbox-explorer.html` |

```
python build.py
```

The build checks every reference first (a part without a position, a wire to an unknown part,
a walkthrough step naming a missing wire) and writes nothing if one is broken.

Wires are routed automatically: each connection picks the facing sides of its two parts, ends
are spread along each side, straight runs are preferred, and wires that cross a supply bar hop
over it. Where the automatic route is not good enough, `layout.json` pins the ends or gives
waypoints.

To change the system, edit `skeleton.json` (structure) and `texts.json` (words), then rebuild.
