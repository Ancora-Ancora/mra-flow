import json
import re
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

PAYLOAD = Path(__file__).resolve().parent.parent / "payload"

# A `bd create` command, possibly continued over several lines with `\`.
BD_CREATE = re.compile(r"bd create(?:[^\n`]|\\\n)*")


class BdCreateCommandsTest(unittest.TestCase):
    def test_no_parent_and_discovered_from_on_the_same_issue(self):
        # bd rejects `--parent X --deps discovered-from:X`: the parent-child
        # link already exists, so the second dependency on X fails the create.
        offenders = []
        for path in sorted(PAYLOAD.rglob("*.md")):
            for command in BD_CREATE.findall(path.read_text(encoding="utf-8")):
                parent = re.search(r"--parent (\S+)", command)
                found = re.search(r"discovered-from:([^\s`\"]+)", command)
                if parent and found and parent.group(1) == found.group(1):
                    offenders.append(f"{path.relative_to(PAYLOAD)}: {command.strip()}")
        self.assertEqual(offenders, [])


SKILLS = PAYLOAD / "orchestrator" / ".claude" / "skills"


class PlanCheckTest(unittest.TestCase):
    def test_shared_plan_check_section_exists_and_is_referenced(self):
        # mra-update, mra-verify and mra-archive point to the Plan check of
        # mra-track by its heading: renaming it silently breaks them.
        track = (SKILLS / "mra-track" / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("\n## Plan check\n", track)
        for skill in ("mra-update", "mra-verify", "mra-archive"):
            text = (SKILLS / skill / "SKILL.md").read_text(encoding="utf-8")
            self.assertIn("*Plan check* of `/mra-track`", text, skill)

    def test_task_issues_carry_task_metadata(self):
        # The task -> issue link is the `task` metadata, not an append-only
        # map in the epic notes.
        track = (SKILLS / "mra-track" / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn('--metadata \'{"task":"X.Y"}\'', track)
        self.assertNotIn("--append-notes \"tasks.md map", track)


QA_UI = PAYLOAD / "orchestrator" / ".mra-flow" / "qa-ui" / "smoke.mjs"


class QaUiTest(unittest.TestCase):
    def skill(self, name):
        return (SKILLS / name / "SKILL.md").read_text(encoding="utf-8")

    def test_skills_that_run_the_qa_ui_steps_point_to_its_file(self):
        # mra-qa-ui has disable-model-invocation: callers follow its file.
        for name in ("mra-verify", "mra-hotfix"):
            self.assertIn("`.claude/skills/mra-qa-ui/SKILL.md`", self.skill(name), name)
        self.assertIn("qa-ui:", self.skill("mra-archive"))

    def test_qa_ui_findings_enter_the_bug_flow(self):
        text = self.skill("mra-qa-ui")
        creates = BD_CREATE.findall(text)
        in_scope = [c for c in creates if "--parent <epic>" in c]
        self.assertTrue(in_scope)
        for command in in_scope:
            self.assertIn("-t bug", command)
            self.assertIn("verify,qa-ui", command)
        self.assertTrue(any("needs-triage" in c and "--parent" not in c for c in creates))

    def test_plan_example_is_valid_json_for_the_runner(self):
        text = self.skill("mra-qa-ui")
        block = re.search(r"```json\n(.*?)```", text, re.S).group(1)
        plan = json.loads(block)
        self.assertIsInstance(plan["baseUrl"], str)
        for page in plan["pages"]:
            role = page.get("role", "anonymous")
            self.assertTrue(role == "anonymous" or role in plan["roles"], role)
        self.assertIn("smoke.mjs", text)

    @unittest.skipUnless(shutil.which("node"), "node not installed")
    def test_runner_parses_and_rejects_a_bad_plan(self):
        done = subprocess.run(["node", "--check", str(QA_UI)], capture_output=True, text=True)
        self.assertEqual(done.returncode, 0, done.stderr)
        with tempfile.TemporaryDirectory() as tmp:
            plan = Path(tmp) / "plan.json"
            plan.write_text('{"baseUrl": "http://localhost", "pages": [{"path": "/", "role": "ghost"}]}')
            done = subprocess.run(["node", str(QA_UI), str(plan)], capture_output=True, text=True, cwd=tmp)
        self.assertEqual(done.returncode, 2)
        self.assertIn("unknown role ghost", done.stderr)


if __name__ == "__main__":
    unittest.main()


UI_PREVIEW = PAYLOAD / "orchestrator" / ".mra-flow" / "docs" / "agents" / "ui-preview.md"


class UiPreviewTest(unittest.TestCase):
    def test_rule_file_exists_and_names_the_three_previews(self):
        text = UI_PREVIEW.read_text(encoding="utf-8")
        for line in ("preview: prototype docs/prototypes/<slug>.md", "preview: sketch accepted", "preview: declined (<reason>)"):
            self.assertIn(line, text)

    def test_skills_that_ask_or_use_the_preview_point_to_the_rule(self):
        # One definition of "which screen needs which preview": every skill
        # that asks for a preview or reads its outcome points to the same file.
        for name in ("mra-roadmap", "mra-grill", "mra-propose", "mra-update", "mra-prototype"):
            text = (SKILLS / name / "SKILL.md").read_text(encoding="utf-8")
            self.assertIn("`.mra-flow/docs/agents/ui-preview.md`", text, name)

    def test_prototype_verdict_is_written_to_a_note(self):
        text = (SKILLS / "mra-prototype" / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("docs/prototypes/<slug>.md", text)
        qa = (SKILLS / "mra-qa-ui" / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("docs/prototypes/<slug>.md", qa)

    def test_build_does_not_ask_for_a_preview(self):
        text = (SKILLS / "mra-build" / "SKILL.md").read_text(encoding="utf-8")
        self.assertNotIn("ui-preview.md", text)


ROADMAP = PAYLOAD / "orchestrator" / ".mra-flow" / "docs" / "agents" / "roadmap.md"


class RoadmapTest(unittest.TestCase):
    def skill(self, name):
        return (SKILLS / name / "SKILL.md").read_text(encoding="utf-8")

    def test_rule_file_defines_estimates_totals_actuals_and_beads(self):
        text = ROADMAP.read_text(encoding="utf-8")
        for heading in ("## The file", "## Totals", "## Actuals", "## Beads", "## Who writes what"):
            self.assertIn(f"\n{heading}\n", text)
        # ADR-0011: effort in effective hours, never days.
        for column in ("Estimate (h)", "Confidence", "Revised (h)", "Actual (h)"):
            self.assertIn(column, text)
        self.assertNotIn("(d)", text)
        for line in ("`Estimate: <min>–<max> h`", "`Forecast: <min>–<max> h`", "`Progress: "):
            self.assertIn(line, text)

    def test_skills_use_mra_effort_for_the_figures(self):
        # Totals, actuals and the variance report come from the script, not
        # from agent arithmetic.
        self.assertIn("mra-effort measure", self.skill("mra-archive"))
        self.assertIn("mra-effort record", self.skill("mra-archive"))
        for name in ("mra-archive", "mra-propose", "mra-roadmap"):
            self.assertIn("mra-effort report", self.skill(name), name)
            self.assertNotIn("(d)", self.skill(name), name)

    def test_slice_epics_carry_the_estimate(self):
        # bd shows the estimate next to the work: the slice epic holds the
        # upper bound of the current range, in minutes.
        self.assertIn("--estimate", ROADMAP.read_text(encoding="utf-8"))
        self.assertIn("--estimate", self.skill("mra-roadmap"))
        self.assertIn("--estimate", self.skill("mra-propose"))

    def test_skills_that_read_or_write_a_roadmap_point_to_the_rule(self):
        # One definition of the roadmap format: every skill that touches a
        # roadmap points to the same file.
        for name in ("mra-roadmap", "mra-grill", "mra-propose", "mra-track", "mra-archive"):
            self.assertIn("`.mra-flow/docs/agents/roadmap.md`", self.skill(name), name)

    def test_roadmap_skill_has_all_modes_and_is_user_invoked(self):
        text = self.skill("mra-roadmap")
        self.assertIn("disable-model-invocation: true", text)
        for mode in ("--from <map-epic>", "--retro <initiative>", "**revise**"):
            self.assertIn(mode, text)

    def test_slice_epics_are_found_by_slice_metadata_as_json(self):
        # Same pitfall as the task metadata: a JSON string, never --set-metadata.
        text = ROADMAP.read_text(encoding="utf-8")
        self.assertIn("--metadata '{\"slice\":\"<change-id>\"}'", text)
        self.assertIn("--metadata-field slice=<change-id>", text)
        self.assertNotIn("--set-metadata slice", text)

    def test_roadmap_may_create_issues(self):
        claude = (PAYLOAD / "orchestrator" / ".mra-flow" / "CLAUDE.md").read_text(encoding="utf-8")
        self.assertIn("only in `/mra-roadmap` (initiative and slice epics, never tasks)", claude)

    def test_roadmap_recommends_prototype_and_research_only_for_cut_or_size(self):
        text = self.skill("mra-roadmap")
        self.assertIn("**Stuck questions.**", text)
        self.assertIn("`/mra-research <question>`", text)
        self.assertIn("`/mra-prototype <question>`", text)
        self.assertIn("changes the cut", text)

    def test_ui_preview_cell_can_point_to_a_done_prototype(self):
        rule = ROADMAP.read_text(encoding="utf-8")
        self.assertIn("`prototype docs/prototypes/<slug>.md`", rule)
        self.assertIn("UI preview* cell", self.skill("mra-grill"))

    def test_grill_suggests_a_roadmap_before_and_after(self):
        text = self.skill("mra-grill")
        self.assertEqual(text.count("`/mra-roadmap <topic>`"), 2)

    def test_late_phases_recommend_retro_once(self):
        rule = ROADMAP.read_text(encoding="utf-8")
        self.assertIn("\n## A roadmap found missing late\n", rule)
        self.assertIn("roadmap: declined (<reason>)", rule)
        for name in ("mra-propose", "mra-archive"):
            text = self.skill(name)
            self.assertIn("*A roadmap found missing late*", text, name)
            self.assertIn("`/mra-roadmap --retro <initiative>` once", text, name)


MODEL_DISPLAY = PAYLOAD / "orchestrator" / ".mra-flow" / "docs" / "agents" / "model-display.md"


class ModelDisplayTest(unittest.TestCase):
    def test_rule_file_defines_the_model_line(self):
        text = MODEL_DISPLAY.read_text(encoding="utf-8")
        self.assertIn("`Model: <model> (<role>)`", text)
        self.assertIn("subagentStatusLine", text)

    def test_every_phase_skill_points_to_the_rule(self):
        # The user always sees which model runs each phase and each subagent:
        # every mra-* skill points to the same rule.
        for path in sorted(SKILLS.glob("mra-*/SKILL.md")):
            self.assertIn("`.mra-flow/docs/agents/model-display.md`", path.read_text(encoding="utf-8"), path.parent.name)

    def test_build_progress_block_has_a_model_line(self):
        text = (SKILLS / "mra-build" / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("Model          ", text)
        self.assertIn("three-line progress block", text)


class ModelRecordTest(unittest.TestCase):
    def test_models_are_recorded_on_the_issue(self):
        # Which model did each task's work stays on the issue, after the
        # conversation is gone.
        rule = MODEL_DISPLAY.read_text(encoding="utf-8")
        self.assertIn("\n## Record\n", rule)
        self.assertIn("--set-metadata models=", rule)
        for name in ("mra-build", "mra-fix", "mra-hotfix", "mra-verify"):
            text = (SKILLS / name / "SKILL.md").read_text(encoding="utf-8")
            self.assertIn("--set-metadata models=", text, name)


class EffortBreakdownSkillTest(unittest.TestCase):
    def test_archive_shows_the_breakdown(self):
        text = (SKILLS / "mra-archive" / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("mra-effort breakdown <change-id>", text)
        self.assertIn("every change", text)

    def test_build_names_the_bd_id_in_dispatch_prompts(self):
        text = (SKILLS / "mra-build" / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("name the bd id in every dispatch prompt", text)
        self.assertIn("mra-effort breakdown", text)
