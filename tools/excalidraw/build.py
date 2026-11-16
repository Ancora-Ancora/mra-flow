"""Build mra-flow.excalidraw: the phase diagram laid out by hand, sections 2 and 3 from layout.json (extract.cjs)."""
import json, random, sys
random.seed(11)
L = json.load(open("layout.json"))
FONT = 6  # Nunito
INK, MUTED = "#1e1e1e", "#495057"
COL = {"OS": "#a5d8ff", "SP": "#b2f2bb", "MP": "#ffec99", "CU": "#d0bfff"}
NAME = {"OS": "OpenSpec", "SP": "superpowers", "MP": "Matt Pocock", "CU": "custom"}
els = []
def base(t, x, y, w, h, **kw):
    e = {"id": f"{t[:2]}{len(els)}", "type": t, "x": round(x, 1), "y": round(y, 1), "width": round(w, 1), "height": round(h, 1),
         "angle": 0, "strokeColor": INK, "backgroundColor": "transparent", "fillStyle": "solid", "strokeWidth": 1.5,
         "strokeStyle": "solid", "roughness": 1, "opacity": 100, "groupIds": [], "frameId": None, "roundness": {"type": 3},
         "seed": random.randint(1, 2**31), "version": 1, "versionNonce": random.randint(1, 2**31), "isDeleted": False,
         "boundElements": [], "updated": 1, "link": None, "locked": False}
    e.update(kw)
    e["strokeSharpness"] = "round" if e.get("roundness") else "sharp"
    els.append(e); return e
def tw(s, fs): return len(s) * fs * 0.56
def text(s, cx, y, fs, color=INK, gid=None, align="center", x=None):
    w = tw(s, fs); h = fs * 1.25
    return base("text", (cx - w / 2) if x is None else x, y, w, h, text=s, originalText=s, fontSize=fs, fontFamily=FONT,
                textAlign=align, verticalAlign="top", containerId=None, lineHeight=1.25, baseline=round(fs * 0.95),
                autoResize=True, strokeColor=color, groupIds=[gid] if gid else [], roundness=None, strokeWidth=1)

# ---------- title + legend ----------
text("mra-flow", 0, 0, 40, x=0, align="left")
text("Workflow of the orchestrator: commands, the skills they call, and how they hand over.", 0, 56, 18, MUTED, x=0, align="left")
lx, ly = 0, 100
legend = [("OS", "OpenSpec"), ("SP", "superpowers"), ("MP", "Matt Pocock"), ("CU", "custom mra-* logic")]
for k, label in legend:
    base("rectangle", lx, ly, 34, 22, backgroundColor=COL[k], roughness=0)
    text(label, 0, ly + 1, 16, x=lx + 42, align="left"); lx += 42 + tw(label, 16) + 36
base("rectangle", lx, ly, 34, 22, backgroundColor="#ffffff", roughness=0)
for i, k in enumerate(("OS", "SP", "CU")): base("rectangle", lx + 4 + i * 9, ly + 5, 8, 12, backgroundColor=COL[k], strokeColor="transparent", roughness=0, roundness=None)
text("mixed: one band per family", 0, ly + 1, 16, x=lx + 42, align="left"); lx += 42 + tw("mixed: one band per family", 16) + 36
base("rectangle", lx, ly, 34, 22, backgroundColor="#ffffff", strokeStyle="dashed", roughness=0)
text("dashed: on demand", 0, ly + 1, 16, x=lx + 42, align="left"); lx += 42 + tw("dashed: on demand", 16) + 36
base("arrow", lx, ly + 11, 50, 0, points=[[0, 0], [50, 0]], strokeStyle="dashed", strokeColor="#868e96", roundness=None, lastCommittedPoint=None, startArrowhead=None, endArrowhead="arrow", startBinding=None, endBinding=None, elbowed=False)
text("optional hand-over", 0, ly + 1, 16, x=lx + 60, align="left")

# ---------- phase diagram, hand laid out ----------
text("1. Phases", 0, 170, 28, x=0, align="left")
N = {
 "explore":  ("/mra-explore", "optional", [("OS", ["openspec-explore"])], True),
 "grill":    ("/mra-grill", "1 · grill", [("MP", ["grilling", "domain-modeling"])], False),
 "propose":  ("/mra-propose", "2 · propose", [("OS", ["openspec-propose", "openspec-update-change"]), ("MP", ["domain-modeling"])], False),
 "track":    ("/mra-track", "3 · track", [("CU", [])], False),
 "build":    ("/mra-build", "4 · build", [("SP", ["using-git-worktrees", "writing-plans", "subagent-driven-development", "test-driven-development"])], False),
 "verify":   ("/mra-verify", "5 · verify", [("SP", ["verification-before-completion", "receiving-code-review"]), ("MP", ["code-review"]), ("CU", [])], False),
 "qaui":     ("/mra-qa-ui", "verify step · or alone", [("SP", ["verification-before-completion"]), ("CU", [])], True),
 "fix":      ("/mra-fix", "6 · fix", [("SP", ["systematic-debugging", "test-driven-development"]), ("MP", ["diagnosing-bugs"])], False),
 "archive":  ("/mra-archive", "7 · archive", [("OS", ["openspec-archive-change"]), ("SP", ["finishing-a-development-branch"]), ("CU", [])], False),
 "update":   ("/mra-update", "any time", [("OS", ["openspec-update-change"]), ("MP", ["domain-modeling"]), ("CU", [])], False),
 "sync":     ("/mra-sync", "rare", [("OS", ["openspec-sync-specs"])], False),
 "hotfix":   ("/mra-hotfix", "rare · archived feature", [("SP", ["using-git-worktrees", "systematic-debugging", "test-driven-development", "verification-before-completion", "finishing-a-development-branch"]), ("MP", ["diagnosing-bugs"]), ("CU", [])], False),
 "drift":    ("/mra-drift", "any time · read-only", [("CU", [])], True),
 "proto":    ("/mra-prototype", "stuck on design", [("MP", ["prototype", "domain-modeling"])], True),
 "research": ("/mra-research", "stuck on a fact", [("MP", ["research"])], True),
}
P = 420  # column pitch
TOP, MAIN, BOT = 450, 910, 1410
POS = {"explore": (0, TOP), "research": (1, TOP), "update": (2, TOP), "proto": (3, TOP), "sync": (5, TOP),
       "grill": (0, MAIN), "propose": (1, MAIN), "track": (2, MAIN), "build": (3, MAIN), "verify": (4, MAIN), "archive": (5, MAIN),
       "apply": (2, BOT), "qaui": (3, BOT), "fix": (4, BOT), "drift": (5, BOT), "hotfix": (6, BOT)}
box = {}
def node(nid):
    col, cy = POS[nid]; cx = 140 + col * P; gid = "g_" + nid
    if nid == "apply":
        w, h = 200, 90; x, y = cx - w / 2, cy - h / 2
        r = base("rectangle", x, y, w, h, backgroundColor="#ffe3e3", strokeColor="#e03131", groupIds=[gid])
        for a, b in (((0, 0), (w, h)), ((0, h), (w, -h))):
            base("line", x + a[0], y + a[1], w, h, points=[[0, 0], list(b)], strokeColor="#e03131", strokeWidth=2.5, groupIds=[gid], roundness=None,
                 lastCommittedPoint=None, startBinding=None, endBinding=None, startArrowhead=None, endArrowhead=None)
        text("/opsx:apply", cx, y + 18, 20, "#c92a2a", gid); text("blocked: use /mra-build", cx, y + 50, 14, "#c92a2a", gid)
        box[nid] = r; return
    title, sub, fams, dashed = N[nid]
    single = len(fams) == 1
    lines_w = [tw(title, 22), tw(sub, 14)]
    for f, sk in fams: lines_w += [tw(NAME[f], 14)] + [tw(s, 14) for s in sk]
    w = max(lines_w) + 48
    h = 30 + 28 + 22 + sum((22 + 19 * len(sk)) + (10 if not single else 0) for f, sk in fams) + 14
    x, y = cx - w / 2, cy - h / 2
    fill = COL[fams[0][0]] if single else "#ffffff"
    r = base("rectangle", x, y, w, h, backgroundColor=fill, strokeStyle="dashed" if dashed else "solid", groupIds=[gid])
    yy = y + 14
    text(title, cx, yy, 22, INK, gid); yy += 30
    text(sub, cx, yy, 14, MUTED, gid); yy += 28
    for f, sk in fams:
        bh = 22 + 19 * len(sk)
        if not single:
            base("rectangle", x + 12, yy - 4, w - 24, bh + 4, backgroundColor=COL[f], strokeColor="transparent", roughness=0, groupIds=[gid])
        text(NAME[f], cx, yy, 14, INK if not single else MUTED, gid); yy += 22
        for s in sk: text(s, cx, yy, 14, INK, gid); yy += 19
        yy += 0 if single else 10
    box[nid] = r
for nid in POS: node(nid)

def side(r, which):
    x, y, w, h = r["x"], r["y"], r["width"], r["height"]
    return {"t": (x + w / 2, y), "b": (x + w / 2, y + h), "l": (x, y + h / 2), "r": (x + w, y + h / 2)}[which]
def arrow(a, b, label, dashed, via=None, sa=None, sb=None, off=0, lpos=None, offa=None, offb=None):
    ra, rb = box[a], box[b]
    if sa is None:
        dx = (rb["x"] + rb["width"] / 2) - (ra["x"] + ra["width"] / 2); dy = (rb["y"] + rb["height"] / 2) - (ra["y"] + ra["height"] / 2)
        if abs(dy) > abs(dx) * 0.6: sa, sb = ("b", "t") if dy > 0 else ("t", "b")
        else: sa, sb = ("r", "l") if dx > 0 else ("l", "r")
    p0 = list(side(ra, sa)); p1 = list(side(rb, sb))
    oa = off if offa is None else offa; ob = off if offb is None else offb
    if sa in "tb": p0[0] += oa
    else: p0[1] += oa
    if sb in "tb": p1[0] += ob
    else: p1[1] += ob
    pts = [p0] + [list(v) for v in (via or [])] + [p1]
    rel = [[round(px - p0[0], 1), round(py - p0[1], 1)] for px, py in pts]
    xs = [q[0] for q in rel]; ys = [q[1] for q in rel]
    e = base("arrow", p0[0], p0[1], max(xs) - min(xs), max(ys) - min(ys), points=rel,
             strokeColor="#868e96" if dashed else "#343a40", strokeWidth=1.5 if dashed else 2.5, strokeStyle="dashed" if dashed else "solid",
             roundness=None, lastCommittedPoint=None, startArrowhead=None, endArrowhead="arrow",
             startBinding={"elementId": ra["id"], "focus": 0, "gap": 6}, endBinding={"elementId": rb["id"], "focus": 0, "gap": 6}, elbowed=False)
    ra["boundElements"].append({"id": e["id"], "type": "arrow"}); rb["boundElements"].append({"id": e["id"], "type": "arrow"})
    if label:
        if lpos: mx, my = lpos
        else:
            k = len(pts) // 2; q0, q1 = pts[k - 1], pts[k]; mx, my = (q0[0] + q1[0]) / 2, (q0[1] + q1[1]) / 2
        fs = 13; lw = tw(label, fs) + 14
        base("rectangle", mx - lw / 2, my - 11, lw, 22, backgroundColor="#ffffff", strokeColor="#dee2e6", roughness=0, strokeWidth=1)
        text(label, mx, my - 9, fs, MUTED)
cx = lambda n: box[n]["x"] + box[n]["width"] / 2
# main sequence
for a, b in (("grill", "propose"), ("propose", "track"), ("track", "build"), ("build", "verify")): arrow(a, b, None, False)
arrow("verify", "archive", "PASS, no open bugs", False)
arrow("verify", "fix", "bugs open", False, sa="b", sb="t", off=-30, lpos=(cx("verify") - 30 - 55, (MAIN + BOT) / 2 - 40))
arrow("fix", "verify", "re-verify", False, sa="t", sb="b", off=30, lpos=(cx("verify") + 30 + 50, (MAIN + BOT) / 2 - 40))
arrow("verify", "qaui", "ui_paths touched", True, sa="b", sb="t", off=-90, via=[(cx("verify") - 90, BOT - 230), (cx("qaui"), BOT - 230)])
arrow("qaui", "fix", "bugs (qa-ui)", True, sa="r", sb="l", off=40)
arrow("archive", "drift", "drift gate", True, sa="b", sb="t")
arrow("sync", "archive", "specs before archive", True, sa="b", sb="t")
arrow("drift", "fix", "DRIFT-CODE, epic open", True, sa="l", sb="r")
arrow("drift", "hotfix", "DRIFT-CODE, archived", True, sa="r", sb="l", off=-20)
arrow("hotfix", "drift", "fix closed", True, sa="l", sb="r", off=20)
arrow("apply", "build", "use instead", True, sa="t", sb="b", off=-40)
# explore / update
arrow("explore", "grill", "decisions to make", True, sa="b", sb="t")
arrow("explore", "propose", "decisions already recorded", True, sa="b", sb="t", off=45, via=[(cx("explore") + 45, MAIN - 190), (cx("propose") - 70, MAIN - 190)])
arrow("update", "propose", "revise artifacts", True, sa="b", sb="t", off=-60, via=[(cx("update") - 60, MAIN - 230), (cx("propose") + 70, MAIN - 230)])
arrow("update", "track", "reconcile beads", True, sa="b", sb="t")
arrow("update", "proto", "open design question", True, sa="r", sb="l", off=-25)
arrow("proto", "update", "verdict", True, sa="l", sb="r", off=25)
# research loops
arrow("research", "update", "cited note", True, sa="r", sb="l", off=-25)
arrow("update", "research", "external fact", True, sa="l", sb="r", off=25)
arrow("research", "propose", "cited note", True, sa="b", sb="t", off=40, lpos=(cx("research") + 40 + 45, MAIN - 300))
arrow("propose", "research", "external fact", True, sa="t", sb="b", off=5, lpos=(cx("research") + 5 - 55, MAIN - 300))
arrow("research", "grill", "cited note", True, sa="b", sb="t", offa=-80, offb=45, via=[(cx("research") - 80, MAIN - 150), (cx("grill") + 45, MAIN - 150)])
arrow("grill", "research", "external fact", True, sa="t", sb="b", offa=-45, offb=-45, via=[(cx("grill") - 45, MAIN - 110), (cx("research") - 45, MAIN - 110)])
# prototype loop with grill: routed above the top lane
ch = TOP - 170
arrow("grill", "proto", "open design question", True, sa="l", sb="t", offa=-25, offb=0, via=[(-60, MAIN - 25), (-60, ch), (cx("proto"), ch)])
arrow("proto", "grill", "verdict", True, sa="r", sb="l", offa=0, offb=25, via=[(cx("proto") + 220, box["proto"]["y"] + box["proto"]["height"] / 2), (cx("proto") + 220, ch - 40), (-100, ch - 40), (-100, MAIN + 25)], lpos=(cx("proto") - 400, ch - 40))
# long hand-overs to/from drift and hotfix: bottom channels
c1, c2, c3, c4 = BOT + 200, BOT + 250, BOT + 300, BOT + 350
arrow("grill", "drift", "existing capability", True, sa="b", sb="b", via=[(cx("grill") - 30, c1), (cx("drift") - 40, c1)], off=-30, lpos=(cx("propose"), c1))
arrow("propose", "drift", "existing capability", True, sa="b", sb="b", via=[(cx("propose") - 30, c2), (cx("drift"), c2)], off=-30, lpos=(cx("track") + 120, c2))
arrow("drift", "propose", "DRIFT-SPEC", True, sa="b", sb="b", via=[(cx("drift") + 40, c3), (cx("propose") + 30, c3)], off=40, lpos=(cx("build"), c3))
arrow("hotfix", "grill", "spec gap: escalate", True, sa="b", sb="b", via=[(cx("hotfix"), c4), (cx("grill") + 30, c4)], off=0, lpos=(cx("fix"), c4))

# ---------- sections 2 and 3, from the Mermaid layout, restyled ----------
h2 = [h for h in L["headings"] if h["text"].startswith("2.")][0]
y_cut = h2["y"] - 10
dy = (c4 + 160) - h2["y"]; dx = 0
def S(o): return {**o, "x": o["x"] + dx, "y": o["y"] + dy}
for h in L["headings"]:
    if h["y"] >= y_cut:
        h = S(h); text(h["text"], 0, h["y"], 28 if h["text"][:2] in ("2.", "3.") else 20, x=0, align="left")
for c in L["clusters"]:
    if c["y"] < y_cut: continue
    c = S(c); base("rectangle", c["x"], c["y"], c["w"], c["h"], backgroundColor="#fff9db", strokeColor="#fcc419", roughness=0, strokeWidth=1)
    for t in c["texts"]: t = S(t); text(t["text"], t["x"] + t["w"] / 2, t["y"], 16, "#e67700")
nodes2 = []
for i, n in enumerate(L["nodes"]):
    if n["y"] < y_cut: continue
    n = S(n); gid = f"s{i}"
    fill = n["fill"] if n["fill"] not in (None, "transparent") else "transparent"
    r = base("rectangle", n["x"], n["y"], n["w"], n["h"], backgroundColor=fill, strokeColor=n["stroke"] or INK,
             strokeStyle="dashed" if n["dashed"] else "solid", groupIds=[gid])
    nodes2.append(r)
    for bd in n["bands"]:
        bd = S(bd); base("rectangle", bd["x"] - 4, bd["y"] - 1, bd["w"] + 8, bd["h"] + 2, backgroundColor=bd["fill"], strokeColor="transparent", roughness=0, groupIds=[gid])
    for t in n["texts"]:
        t = S(t); text(t["text"], t["x"] + t["w"] / 2, t["y"], t["size"] + (2 if t["size"] > 17 else 0), t.get("color") or INK, gid)
def near(pt):
    best, bd = None, 25
    for r in nodes2:
        ddx = max(r["x"] - pt[0], 0, pt[0] - (r["x"] + r["width"])); ddy = max(r["y"] - pt[1], 0, pt[1] - (r["y"] + r["height"]))
        d = (ddx * ddx + ddy * ddy) ** .5
        if d < bd: best, bd = r, d
    return best
for e in L["edges"]:
    pts = [[px + dx, py + dy] for px, py in e["pts"]]
    if pts[0][1] < y_cut + dy: continue
    x0, y0 = pts[0]; rel = [[round(px - x0, 1), round(py - y0, 1)] for px, py in pts]
    xs = [q[0] for q in rel]; ys = [q[1] for q in rel]
    a = base("arrow", x0, y0, max(xs) - min(xs), max(ys) - min(ys), points=rel, strokeColor="#868e96" if e["dashed"] else "#343a40",
             strokeStyle="dashed" if e["dashed"] else "solid", strokeWidth=1.5 if e["dashed"] else 2, roundness={"type": 2},
             lastCommittedPoint=None, startArrowhead=None, endArrowhead="arrow" if e["arrow"] else None, startBinding=None, endBinding=None, elbowed=False)
    for key, pt in (("startBinding", pts[0]), ("endBinding", pts[-1])):
        r = near(pt)
        if r: a[key] = {"elementId": r["id"], "focus": 0, "gap": 4}; r["boundElements"].append({"id": a["id"], "type": "arrow"})
for t in L["labels"]:
    if t["y"] < y_cut: continue
    t = S(t); lw = tw(t["text"], 13) + 14
    base("rectangle", t["x"] + t["w"] / 2 - lw / 2, t["y"] - 2, lw, t["h"] + 4, backgroundColor="#ffffff", strokeColor="#dee2e6", roughness=0, strokeWidth=1)
    text(t["text"], t["x"] + t["w"] / 2, t["y"], 13, MUTED)
doc = {"type": "excalidraw", "version": 2, "source": "mra-flow (generated from .mra-flow/docs/mra-flow.md)", "elements": els,
       "appState": {"viewBackgroundColor": "#ffffff", "gridSize": None, "currentItemFontFamily": FONT}, "files": {}}
json.dump(doc, open(sys.argv[1], "w"), indent=1)
print(len(els), "elements")
