"""Write x.html: the Mermaid blocks and headings of mra-flow.md, rendered 1:1 for extract.cjs."""
import html
from pathlib import Path

DOC = Path(__file__).resolve().parents[2] / "payload/orchestrator/.mra-flow/docs/mra-flow.md"
src = DOC.read_text(encoding="utf-8").splitlines()
out, i, k = [], 0, 0
while i < len(src):
    line = src[i]
    if line.startswith("```mermaid"):
        j = i + 1
        while src[j] != "```":
            j += 1
        out.append(f'<pre class="mermaid" id="d{k}">{html.escape(chr(10).join(src[i + 1:j]))}</pre>')
        k, i = k + 1, j
    elif line.startswith(("# ", "## ", "### ")):
        level = len(line.split(" ")[0])
        out.append(f'<h{level} class="hd">{html.escape(line[level + 1:])}</h{level}>')
    i += 1
Path(__file__).with_name("x.html").write_text(
    '<html><head><meta charset="utf-8"></head><body style="background:#fff;margin:40px;font-family:Helvetica,Arial,sans-serif">'
    + "".join(out)
    + '<script src="node_modules/mermaid/dist/mermaid.min.js"></script><script>'
    "mermaid.initialize({startOnLoad:false,flowchart:{useMaxWidth:false}});"
    "mermaid.run().then(()=>window.done=1).catch(e=>{window.err=String(e);window.done=1});</script></body></html>",
    encoding="utf-8")
