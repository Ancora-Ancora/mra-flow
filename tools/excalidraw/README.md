# mra-flow.excalidraw generator

Regenerates `payload/orchestrator/.mra-flow/docs/mra-flow.excalidraw` from `mra-flow.md`. Run it after every change to the diagrams of `mra-flow.md`:

```bash
tools/excalidraw/generate.sh
```

How it works: `prepare.py` puts the Mermaid blocks of `mra-flow.md` in `x.html`; `extract.cjs` renders them with Mermaid in headless Chromium (Playwright) and saves node, band, edge and label positions to `layout.json`; `build.py` writes the Excalidraw file.

- **Phase diagram (section 1)** is laid out by hand in `build.py` (`N`, `POS` and the `arrow(...)` calls), not taken from Mermaid: when a command, a skill it calls or a hand-over in the phase diagram changes, update those too.
- **Sections 2 and 3** follow the Mermaid layout and need no edits.
- Check the result in Excalidraw (excalidraw.com, or the `pomdtr.excalidraw-editor` VS Code extension) before committing.
