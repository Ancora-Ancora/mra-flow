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
        for name in ("mra-grill", "mra-propose", "mra-update", "mra-prototype"):
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
