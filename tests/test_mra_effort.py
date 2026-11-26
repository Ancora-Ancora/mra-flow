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

    def test_record_fills_an_empty_actuals_section(self):
        # A roadmap may carry the heading before the first actual: record must reuse it, not add another.
        self.write_roadmap(ROADMAP.replace("## Total", "## Actuals by phase\n\n## Total"))
        self.run_effort("record", "demo", "add-a", "--phase", "build=1")
        done = self.run_effort("record", "demo", "add-b", "--phase", "fix=2")
        self.assertEqual(done.returncode, 0, done.stderr)
        text = self.roadmap()
        self.assertEqual(text.count("## Actuals by phase"), 1)
        self.assertEqual(text.count("| Change id | grill |"), 1)
        self.assertRegex(text, r"\| add-a \|.*\n\| add-b \|")

    def test_report_without_estimates_says_so(self):
        self.write_roadmap(re.sub(r"\| (5–8|2–4|8–12) \|", "|  |", ROADMAP))
        self.run_effort("report", "demo")
        self.assertIn("- Estimate: – h", self.roadmap())

    def test_report_variance_against_the_upper_bound(self):
        self.write_roadmap()
        self.run_effort("record", "demo", "add-a", "--phase", "build=10")   # 8 estimated: +2, +25%
        self.run_effort("record", "demo", "add-b", "--phase", "fix=3")      # 4 estimated: -1, -25%
        done = self.run_effort("report", "demo")
        self.assertEqual(done.returncode, 0, done.stderr)
        report = (self.orch / "docs/roadmap/demo-effort.md").read_text()
        self.assertIn("do not edit", report)
        self.assertIn("| 1 | bd-2 | add-a | First slice | 5–8 | 8 | 10 | +2.0 | +25% | 🔴 | 10 |  |", report)
        self.assertIn("| 2 | bd-3 | add-b | Second slice | 2–4 | 4 | 3 | -1.0 | -25% | 🟢 |  | 3 |", report)
        self.assertIn("| 3 | bd-4 | add-c | Third slice | 8–12 | 12 | – |  |  | ⚪ |  |  |", report)
        self.assertNotIn("add-d", report)
        self.assertIn("| **Total** | done slices |  | 12 | 13 | +1.0 | +8% | 🔴 | 10 | 3 |", report)
        # one column per phase used, named after its command, in workflow order
        self.assertIn("| Variance (h) | Variance (%) |  | mra-build | mra-fix |", report)
        self.assertNotIn("mra-grill", report)
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

    # ---------------------------------------------------------------- breakdown

    PLAN = """# Plan

### Task 1: [bd-11] Build the thing

body

### Task 2: [bd-12] Wire the other thing
"""

    def assistant(self, minutes, model, inp, cc, cr, out, msg_id):
        return {"type": "assistant", "timestamp": at(minutes), "message": {
            "role": "assistant", "id": msg_id, "model": model, "content": "ok",
            "usage": {"input_tokens": inp, "cache_creation_input_tokens": cc,
                      "cache_read_input_tokens": cr, "output_tokens": out}}}

    def breakdown_fixture(self):
        (self.orch / "openspec/changes/add-a/plan.md").write_text(self.PLAN)
        main = [command(0, "mra-build", "add-a"),
                self.assistant(2, "claude-opus-5-5-20260101", 10, 0, 0, 90, "m1"),
                tick(30)]
        implementer = [user(5, "Implement bd-11 in the worktree for add-a"),
                       self.assistant(8, "claude-sonnet-5-5", 100, 200, 300, 400, "a1"),
                       self.assistant(8, "claude-sonnet-5-5", 100, 200, 300, 450, "a1"),  # duplicate id: last wins
                       self.assistant(12, "claude-sonnet-5-5", 0, 0, 0, 50, "a2")]
        reviewer = [user(14, "Review .superpowers/sdd/plan-add-a/task-1-brief.md"),
                    self.assistant(16, "claude-haiku-5-5", 0, 0, 100, 100, "r1")]
        final = [user(20, "Final review of add-a"),
                 self.assistant(24, "claude-opus-5-5", 0, 0, 0, 200, "f1")]
        self.session("s1", main)
        sub = self.logs / "s1" / "subagents"
        sub.mkdir(parents=True)
        for name, records in (("agent-i", implementer), ("agent-r", reviewer), ("agent-f", final)):
            (sub / f"{name}.jsonl").write_text("\n".join(json.dumps(r) for r in records) + "\n")

    def breakdown(self, *extra):
        self.breakdown_fixture()
        done = self.run_effort("breakdown", "add-a", "--logs", str(self.logs), "--json", *extra)
        self.assertEqual(done.returncode, 0, done.stderr)
        return json.loads(done.stdout)

    def test_breakdown_attributes_subagents_to_tasks(self):
        data = self.breakdown()
        rows = {r["key"]: r for r in data["rows"]}
        self.assertEqual(list(rows), ["1", "2", "other", "session"])
        task1 = rows["1"]
        self.assertEqual(task1["bd_id"], "bd-11")
        self.assertEqual(task1["title"], "Build the thing")
        # implementer (named by bd id): 5..12 = 7 min; reviewer (task-1-brief path): 2 min
        self.assertAlmostEqual(task1["hours"], 9 / 60, places=2)
        models = {m["model"]: m for m in task1["models"]}
        self.assertEqual(models["Sonnet 5.5"]["tokens"], 100 + 200 + 300 + 450 + 50)
        self.assertEqual(models["Sonnet 5.5"]["output_tokens"], 500)
        self.assertEqual(models["Haiku 5.5"]["tokens"], 200)
        self.assertAlmostEqual(models["Haiku 5.5"]["share"], 200 / 1300, places=3)
        self.assertEqual(rows["2"]["models"], [])
        self.assertEqual(rows["other"]["models"][0]["model"], "Opus 5.5")
        self.assertEqual(rows["other"]["models"][0]["tokens"], 200)
        self.assertEqual(rows["session"]["models"][0]["tokens"], 100)

    def test_breakdown_epic_totals(self):
        data = self.breakdown()
        epic = data["epic"]
        self.assertAlmostEqual(epic["hours"], 30 / 60, places=2)  # the build command, 0..30
        self.assertEqual(epic["tokens"], 1100 + 200 + 200 + 100)
        models = {m["model"]: m for m in epic["models"]}
        self.assertEqual(models["Sonnet 5.5"]["tokens"], 1100)
        self.assertAlmostEqual(models["Sonnet 5.5"]["share"], 1100 / 1600, places=3)
        self.assertEqual(models["Opus 5.5"]["tokens"], 300)
        self.assertAlmostEqual(epic["task_hours"], 9 / 60, places=2)

    def test_breakdown_text_is_a_markdown_table(self):
        self.breakdown_fixture()
        done = self.run_effort("breakdown", "add-a", "--logs", str(self.logs))
        self.assertEqual(done.returncode, 0, done.stderr)
        lines = done.stdout.splitlines()
        self.assertEqual(lines[0], "| Item | Time (h) | Model | Tokens | Output tokens | Share |")
        self.assertIn("**add-a** (epic)", done.stdout)
        self.assertIn("Task 1 [bd-11] Build the thing", done.stdout)
        self.assertIn("1,100", done.stdout)
        self.assertIn("69%", done.stdout)

    def test_breakdown_without_plan_still_reports_other(self):
        self.breakdown_fixture()
        (self.orch / "openspec/changes/add-a/plan.md").unlink()
        done = self.run_effort("breakdown", "add-a", "--logs", str(self.logs), "--json")
        self.assertEqual(done.returncode, 0, done.stderr)
        rows = [r["key"] for r in json.loads(done.stdout)["rows"]]
        self.assertEqual(rows, ["other", "session"])

    def sub_agent(self, name, records):
        sub = self.logs / "s1" / "subagents"
        sub.mkdir(parents=True, exist_ok=True)
        (sub / f"{name}.jsonl").write_text("\n".join(json.dumps(r) for r in records) + "\n")

    def rows_after(self, *agents):
        (self.orch / "openspec/changes/add-a/plan.md").write_text(self.PLAN + "\n### Task 10: [bd-110] Tenth\n")
        self.session("s1", [command(0, "mra-build", "add-a"), tick(30)])
        for name, records in agents:
            self.sub_agent(name, records)
        done = self.run_effort("breakdown", "add-a", "--logs", str(self.logs), "--json")
        self.assertEqual(done.returncode, 0, done.stderr)
        return {r["key"]: r for r in json.loads(done.stdout)["rows"]}

    def test_breakdown_uses_only_the_first_user_message(self):
        later = [user(5, "Review the add-a work"),
                 self.assistant(6, "claude-sonnet-5-5", 0, 0, 0, 10, "x1"),
                 user(7, "tool result mentions bd-12 and plan-add-a/task-2-brief.md")]
        rows = self.rows_after(("agent-l", later))
        self.assertNotIn("bd-12", [r["bd_id"] for r in rows.values() if r["models"]])
        self.assertEqual(rows["2"]["models"], [])
        self.assertEqual(rows["other"]["models"][0]["tokens"], 10)

    def test_task_path_fallback_needs_this_changes_plan_folder(self):
        agent = [user(5, "Review add-a using .superpowers/sdd/plan-other-change/task-2-brief.md"),
                 self.assistant(6, "claude-sonnet-5-5", 0, 0, 0, 10, "x1")]
        rows = self.rows_after(("agent-p", agent))
        self.assertEqual(rows["2"]["models"], [])
        self.assertEqual(rows["other"]["models"][0]["tokens"], 10)

    def test_bd_ids_match_as_whole_tokens(self):
        agent = [user(5, "Implement bd-110 for add-a"),
                 self.assistant(6, "claude-sonnet-5-5", 0, 0, 0, 10, "x1")]
        rows = self.rows_after(("agent-t", agent))
        self.assertEqual(rows["10"]["models"][0]["tokens"], 10)
        self.assertEqual(rows["1"]["models"], [])

