import json
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

from tests.support import REPO_ROOT, TmpTestCase

SCRIPT = REPO_ROOT / "payload" / "orchestrator" / ".mra-flow" / "bin" / "mra-effort"
T0 = datetime(2026, 11, 20, 9, 0, tzinfo=timezone.utc)

ROADMAP = """---
initiative: demo
title: Demo initiative
status: active
epic: bd-1
created: 2026-11-20
---

# Demo initiative

## Slices

| # | Change id | Goal | Repos | Contract | Depends on | UI preview | Size | Estimate (h) | Confidence | Revised (h) | Status | Epic | Actual (h) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | add-a | First slice | be | no | – | – | M | 5–8 | medium | | done | bd-2 | |
| 2 | add-b | Second slice | be | no | 1 | – | S | 2–4 | high | | done | bd-3 | |
| 3 | add-c | Third slice | be | no | 1 | – | L | 8–12 | low | 9–13 | planned | bd-4 | |
| 4 | add-d | Dropped slice | be | no | 1 | – | S | 2–4 | low | | dropped | bd-5 | |

## Total

- Estimate: old
- Forecast: old

## Log

- 2026-11-20 created
"""


def at(minutes: float) -> str:
    return (T0 + timedelta(minutes=minutes)).isoformat().replace("+00:00", "Z")


def user(minutes: float, text: str) -> dict:
    return {"type": "user", "timestamp": at(minutes), "message": {"role": "user", "content": text}}


def command(minutes: float, name: str, args: str = "") -> dict:
    return user(minutes, f"<command-message>{name}</command-message>\n<command-name>/{name}</command-name>"
                         f"\n<command-args>{args}</command-args>")


def tick(minutes: float) -> dict:
    return {"type": "assistant", "timestamp": at(minutes), "message": {"role": "assistant", "content": "ok"}}


class MraEffortTest(TmpTestCase):
    def setUp(self):
        super().setUp()
        self.orch = self.tmp / "orch"
        (self.orch / ".mra-flow/bin").mkdir(parents=True)
        shutil.copy2(SCRIPT, self.orch / ".mra-flow/bin/mra-effort")
        (self.orch / "docs/roadmap").mkdir(parents=True)
        (self.orch / "openspec/changes/archive/2026-11-01-add-other").mkdir(parents=True)
        (self.orch / "openspec/changes/add-a").mkdir()
        self.logs = self.tmp / "logs"
        self.logs.mkdir()

    def session(self, name: str, records: list[dict], subagent: list[dict] | None = None):
        (self.logs / f"{name}.jsonl").write_text("\n".join(json.dumps(r) for r in records) + "\n")
        if subagent:
            sub = self.logs / name / "subagents"
            sub.mkdir(parents=True)
            (sub / "agent-x.jsonl").write_text("\n".join(json.dumps(r) for r in subagent) + "\n")

    def run_effort(self, *args, env=None):
        return subprocess.run([sys.executable, str(self.orch / ".mra-flow/bin/mra-effort"), *args],
                              capture_output=True, text=True, env=env)

    def measure(self, *extra):
        done = self.run_effort("measure", "add-a", "--logs", str(self.logs), "--json", *extra)
        self.assertEqual(done.returncode, 0, done.stderr)
        return json.loads(done.stdout)

    # ---------------------------------------------------------------- measure

    def test_active_time_per_phase_skips_long_pauses(self):
        self.session("s1", [
            command(0, "mra-build", "add-a"), tick(5), tick(10),   # 10 min of build
            tick(60),                                               # 50-min pause: not counted
            tick(66),                                               # 6 min of build
            command(70, "mra-verify", "add-a"), tick(79),          # 4 min of build, then 9 of verify
        ])
        result = self.measure()
        self.assertAlmostEqual(result["phases"]["build"], 20 / 60, places=2)
        self.assertAlmostEqual(result["phases"]["verify"], 9 / 60, places=2)
        self.assertAlmostEqual(result["hours"], 29 / 60, places=1)

    def test_subagent_activity_fills_the_gaps_of_the_main_session(self):
        self.session("s1", [command(0, "mra-build", "add-a"), tick(30)],
                     subagent=[tick(8), tick(16), tick(24)])
        self.assertAlmostEqual(self.measure()["phases"]["build"], 0.5, places=2)

    def test_gap_option(self):
        self.session("s1", [command(0, "mra-build", "add-a"), tick(12)])
        self.assertNotIn("build", self.measure()["phases"])
        self.assertAlmostEqual(self.measure("--gap", "15")["phases"]["build"], 0.2, places=2)

    def test_other_changes_and_unnamed_work(self):
        self.session("s1", [
            command(0, "mra-build", "add-a"), tick(6),
            command(10, "mra-build", "add-other"), tick(18),        # another change: ignored
            command(20, "mra-grill", "a topic"), tick(28),         # unattributed, named by its command
            user(30, "what is pending?"), tick(38),
            command(40, "mra-fix", "add-ab"), tick(45),            # add-ab is not add-a
            command(50, "mra-verify", "add-a"), tick(55),          # closes the change's period
            command(60, "mra-grill", "after"), tick(68),           # after the period: not listed
        ])
        result = self.measure()
        self.assertEqual(set(result["phases"]), {"build", "verify"})
        contexts = [(s["context"], s["prompt"]) for s in result["unattributed"]]
        self.assertIn(("/mra-grill a topic", "what is pending?"), contexts)
        self.assertIn("/mra-fix add-ab", [c for c, _ in contexts])
        self.assertFalse(any("add-other" in c or "after" in c for c, _ in contexts))

    def test_alias_counts_for_the_change(self):
        self.session("s1", [command(0, "mra-hotfix", "bd-77"), tick(9)])
        result = self.measure("--alias", "bd-77")
        self.assertAlmostEqual(result["phases"]["hotfix"], 0.15, places=2)

    def test_default_logs_follow_the_claude_config_dir(self):
        config = self.tmp / "claude"
        project = config / "projects" / re.sub(r"[^A-Za-z0-9]", "-", str(self.orch.resolve()))
        project.mkdir(parents=True)
        (project / "s.jsonl").write_text(json.dumps(command(0, "mra-build", "add-a")) + "\n"
                                         + json.dumps(tick(6)) + "\n")
        env = dict(os.environ, CLAUDE_CONFIG_DIR=str(config))
        done = self.run_effort("measure", "add-a", "--json", env=env)
        self.assertEqual(done.returncode, 0, done.stderr)
        self.assertAlmostEqual(json.loads(done.stdout)["phases"]["build"], 0.1, places=2)

    def test_missing_logs_is_a_refusal(self):
        done = self.run_effort("measure", "add-a", "--logs", str(self.tmp / "nope"))
        self.assertEqual(done.returncode, 1)
        self.assertIn("no Claude Code session logs", done.stderr)

    # ---------------------------------------------------------------- record and report

    def write_roadmap(self, text=ROADMAP):
        (self.orch / "docs/roadmap/demo.md").write_text(text)

    def roadmap(self):
        return (self.orch / "docs/roadmap/demo.md").read_text()

    def test_record_writes_actual_and_phases(self):
        self.write_roadmap()
        done = self.run_effort("record", "demo", "add-a", "--phase", "grill=1.5", "--phase", "build=6",
                               "--phase", "build=0.5")
        self.assertEqual(done.returncode, 0, done.stderr)
        text = self.roadmap()
        self.assertRegex(text, r"\| 1 \| add-a \|.*\| done \| bd-2 \| 8 \|")
        self.assertIn("## Actuals by phase", text)
        self.assertRegex(text, r"\| add-a \| 1\.5 \|(  \|)* 6\.5 \|(  \|)* 8 \|")
        self.assertLess(text.index("## Actuals by phase"), text.index("## Total"))
        # recording again replaces the row; --actual overrides the sum
        self.run_effort("record", "demo", "add-a", "--phase", "build=7", "--actual", "7.5")
        text = self.roadmap()
        self.assertEqual(text.count("| add-a |"), 2)  # one in Slices, one in Actuals by phase
        self.assertRegex(text, r"\| done \| bd-2 \| 7\.5 \|")

    def test_report_variance_against_the_upper_bound(self):
        self.write_roadmap()
        self.run_effort("record", "demo", "add-a", "--phase", "build=10")   # 8 estimated: +2, +25%
        self.run_effort("record", "demo", "add-b", "--phase", "fix=3")      # 4 estimated: -1, -25%
        done = self.run_effort("report", "demo")
        self.assertEqual(done.returncode, 0, done.stderr)
        report = (self.orch / "docs/roadmap/demo-effort.md").read_text()
        self.assertIn("do not edit", report)
        self.assertIn("| 1 | bd-2 | add-a | First slice | 5–8 | 8 | 10 | +2.0 | +25% | 🔴 |", report)
        self.assertIn("| 2 | bd-3 | add-b | Second slice | 2–4 | 4 | 3 | -1.0 | -25% | 🟢 |", report)
        self.assertIn("| 3 | bd-4 | add-c | Third slice | 8–12 | 12 | – |  |  | ⚪ |", report)
        self.assertNotIn("add-d", report)
        self.assertIn("| **Total** | slices with an estimate and an actual |  | 12 | 13 | +1.0 | +8% | 🔴 |", report)
        self.assertIn("## Hours by phase", report)
        self.assertIn("| Change id | build | fix | Total |", report)
        text = self.roadmap()
        self.assertIn("- Estimate: 15–24 h", text)          # dropped slice left out
        self.assertIn("- Forecast: 22–26 h", text)          # 10 + 3 + revised 9–13
        self.assertIn("- Progress: 2/3 slices; actual 13 h vs. estimated 7–12 h", text)
        self.assertNotIn("old", text)
        self.assertIn("## Log", text)

    def test_roadmap_in_days_is_refused(self):
        self.write_roadmap(ROADMAP.replace("(h)", "(d)"))
        done = self.run_effort("report", "demo")
        self.assertEqual(done.returncode, 1)
        self.assertIn("in days", done.stderr)

    def test_unknown_slice_and_phase_are_refused(self):
        self.write_roadmap()
        self.assertEqual(self.run_effort("record", "demo", "add-z", "--phase", "build=1").returncode, 1)
        self.assertEqual(self.run_effort("record", "demo", "add-a", "--phase", "coding=1").returncode, 2)
        self.assertEqual(self.run_effort("report", "nope").returncode, 1)
