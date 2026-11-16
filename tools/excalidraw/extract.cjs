const { chromium } = require("./node_modules/playwright");
// Renders x.html (see prepare.py) and saves the diagram layout to layout.json for build.py.
const fs = require("fs");
(async () => {
  const b = await chromium.launch(); const p = await b.newPage({ viewport: { width: 4000, height: 2000 } });
  await p.goto("file://" + process.cwd() + "/x.html"); await p.waitForFunction(() => window.done, null, { timeout: 30000 });
  const data = await p.evaluate(() => {
    const hex = (c) => { const m = c && c.match(/rgba?\(([\d.]+),\s*([\d.]+),\s*([\d.]+)(?:,\s*([\d.]+))?/); if (!m) return null; if (m[4] !== undefined && +m[4] === 0) return "transparent"; return "#" + [m[1], m[2], m[3]].map(v => (+v).toString(16).padStart(2, "0")).join(""); };
    const R = (r) => ({ x: r.left + scrollX, y: r.top + scrollY, w: r.width, h: r.height });
    const texts = (root) => { const out = []; const w = document.createTreeWalker(root, NodeFilter.SHOW_TEXT); let n;
      while ((n = w.nextNode())) { if (!n.textContent.trim()) continue; const rg = document.createRange(); rg.selectNodeContents(n);
        const cs = getComputedStyle(n.parentElement); const base = { size: parseFloat(cs.fontSize), color: hex(cs.color) || "#1e1e1e" };
        const rects = [...rg.getClientRects()].filter(r => r.width >= 1);
        if (rects.length <= 1) { for (const r of rects) out.push({ ...R(r), text: n.textContent.trim(), ...base }); continue; }
        // wrapped text: split it into the lines the browser laid out
        const str = n.textContent; const lines = []; let cur = null;
        for (let i = 0; i < str.length; i++) { const cr = document.createRange(); cr.setStart(n, i); cr.setEnd(n, i + 1); const r = cr.getClientRects()[0]; if (!r) continue;
          if (!cur || Math.abs(r.top - cur.top) > 2) { cur = { top: r.top, l: r.left, r: r.right, t: r.top, b: r.bottom, s: "" }; lines.push(cur); }
          cur.s += str[i]; cur.l = Math.min(cur.l, r.left); cur.r = Math.max(cur.r, r.right); cur.b = Math.max(cur.b, r.bottom); }
        for (const ln of lines) { const tx = ln.s.trim(); if (!tx) continue; out.push({ x: ln.l + scrollX, y: ln.t + scrollY, w: ln.r - ln.l, h: ln.b - ln.t, text: tx, ...base }); } } return out; };
    const res = { headings: [], clusters: [], nodes: [], edges: [], labels: [] };
    document.querySelectorAll(".hd").forEach(h => res.headings.push({ ...R(h.getBoundingClientRect()), text: h.textContent, size: parseFloat(getComputedStyle(h).fontSize) }));
    document.querySelectorAll("svg g.cluster").forEach(c => { const r = c.querySelector("rect"); const cs = getComputedStyle(r);
      res.clusters.push({ ...R(r.getBoundingClientRect()), fill: hex(cs.fill), stroke: hex(cs.stroke), texts: texts(c.querySelector(".cluster-label") || c) }); });
    document.querySelectorAll("svg g.node").forEach(g => { const s = g.querySelector(":scope > rect, :scope > path, :scope > polygon, :scope > g > path, :scope > g > rect") ; const cs = getComputedStyle(s);
      const bands = [...g.querySelectorAll("span.bos,span.bsp,span.bmp,span.bcu")].map(sp => { const rs = [...sp.getClientRects()]; const x = Math.min(...rs.map(r => r.left)), y = Math.min(...rs.map(r => r.top)), x2 = Math.max(...rs.map(r => r.right)), y2 = Math.max(...rs.map(r => r.bottom)); return { x: x + scrollX, y: y + scrollY, w: x2 - x, h: y2 - y, fill: hex(getComputedStyle(sp).backgroundColor) }; });
      const xs = g.querySelector("span.x"); const blocked = xs ? R(xs.getBoundingClientRect()) : null;
      res.nodes.push({ ...R(s.getBoundingClientRect()), round: s.tagName === "path" || (s.getAttribute("rx") && +s.getAttribute("rx") > 0), fill: hex(cs.fill), stroke: hex(cs.stroke), dashed: cs.strokeDasharray !== "none" && cs.strokeDasharray.split(/[ ,]+/).some(v => parseFloat(v) > 0), bands, blocked, texts: texts(g) }); });
    document.querySelectorAll("svg path.flowchart-link, svg .edgePaths path").forEach(pth => { if (res.edges.find(e => e.el === pth)) return; const L = pth.getTotalLength(); if (!L) return; const M = pth.getScreenCTM(); const pts = [];
      const n = Math.max(2, Math.min(12, Math.round(L / 60))); for (let i = 0; i <= n; i++) { const q = pth.getPointAtLength(L * i / n); const t = new DOMPoint(q.x, q.y).matrixTransform(M); pts.push([t.x + scrollX, t.y + scrollY]); }
      const cs = getComputedStyle(pth); res.edges.push({ pts, dashed: /dotted|dashed/.test(pth.getAttribute("class") || "") || (cs.strokeDasharray !== "none" && cs.strokeDasharray.split(/[ ,]+/).some(v => parseFloat(v) > 0)), arrow: !!pth.getAttribute("marker-end"), stroke: hex(cs.stroke) || "#333333" }); });
    document.querySelectorAll("svg g.edgeLabel").forEach(l => { const t = texts(l); if (t.length) res.labels.push(...t); });
    return res; });
  console.log("err:", await p.evaluate(() => window.err || "none"), "nodes", data.nodes.length, "edges", data.edges.length, "clusters", data.clusters.length, "labels", data.labels.length);
  fs.writeFileSync("layout.json", JSON.stringify(data)); await b.close();
})().catch(e => { console.log("ERR", e.message.split("\n")[0]); process.exit(1); });
