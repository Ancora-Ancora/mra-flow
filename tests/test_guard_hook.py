import json
import subprocess
import sys

from tests.support import REPO_ROOT, TmpTestCase, fake_env

HOOK = REPO_ROOT / "payload/orchestrator/.mra-flow/hooks/guard-installed.py"


class GuardHookTest(TmpTestCase):
    def setUp(self):
        super().setUp()
        self.env = fake_env(self.tmp)
        self.orch = self.tmp / "orch"
        (self.orch / ".mra-flow").mkdir(parents=True)
        (self.orch / "mra-flow.toml").write_text("")
        (self.orch / ".mra-flow/manifest").write_text(json.dumps({"version": "0.1.0", "files": {
            ".claude/skills/mra-drift/SKILL.md": "x", ".mra-flow/hooks/check-drift.py": "y"}}))
        self.src = self.tmp / "src"
        (self.src / "payload/orchestrator").mkdir(parents=True)

    def run_hook(self, path, tool="Edit", source=None, key="file_path"):
        env = dict(self.env, CLAUDE_PROJECT_DIR=str(self.orch),
                   MRA_FLOW_SRC=str(source if source is not None else self.src))
        event = {"tool_name": tool, "tool_input": {key: str(path)}, "cwd": str(self.orch)}
        done = subprocess.run([sys.executable, str(HOOK)], cwd=self.orch, env=env,
                              input=json.dumps(event), capture_output=True, text=True)
        self.assertEqual(done.returncode, 0, done.stderr)
        return json.loads(done.stdout)["hookSpecificOutput"] if done.stdout else None

    def test_installed_file_is_denied_and_points_at_the_source(self):
        out = self.run_hook(self.orch / ".claude/skills/mra-drift/SKILL.md")
        self.assertEqual(out["hookEventName"], "PreToolUse")
        self.assertEqual(out["permissionDecision"], "deny")
        self.assertIn(str(self.src / "payload/orchestrator/.claude/skills/mra-drift/SKILL.md"),
                      out["permissionDecisionReason"])
        self.assertIn("/mra-flow-change", out["permissionDecisionReason"])

    def test_relative_path_resolves_against_cwd(self):
        self.assertIsNotNone(self.run_hook(".mra-flow/hooks/check-drift.py", tool="Write"))

    def test_new_files_in_installed_folders_are_denied(self):
        self.assertIsNotNone(self.run_hook(self.orch / ".claude/skills/mra-mine/SKILL.md", tool="Write"))
        self.assertIsNotNone(self.run_hook(self.orch / ".mra-flow/bin/my-script"))
        self.assertIsNotNone(self.run_hook(self.orch / ".mra-flow/version"))

    def test_state_files_and_project_files_pass(self):
        for rel in (".mra-flow/drift-state.json", ".mra-flow/update-state.json", "docs/adr/0001-x.md",
                    "mra-flow.toml", ".claude/settings.json", ".claude/skills/other/SKILL.md"):
            self.assertIsNone(self.run_hook(self.orch / rel), rel)

    def test_files_outside_the_orchestrator_pass(self):
        self.assertIsNone(self.run_hook(self.src / "payload/orchestrator/.mra-flow/hooks/check-drift.py"))

    def test_notebook_path_is_guarded_too(self):
        self.assertIsNotNone(self.run_hook(self.orch / ".mra-flow/x.ipynb", tool="NotebookEdit",
                                           key="notebook_path"))

    def test_without_a_source_clone_proposes_an_issue(self):
        out = self.run_hook(self.orch / ".mra-flow/hooks/check-drift.py", source=self.tmp / "none")
        self.assertEqual(out["permissionDecision"], "deny")
        self.assertIn("issue", out["permissionDecisionReason"])

    def test_not_an_orchestrator_passes(self):
        (self.orch / "mra-flow.toml").unlink()
        self.assertIsNone(self.run_hook(self.orch / ".mra-flow/hooks/check-drift.py"))

    def test_bad_input_passes(self):
        env = dict(self.env, CLAUDE_PROJECT_DIR=str(self.orch))
        done = subprocess.run([sys.executable, str(HOOK)], env=env, input="{not json",
                              capture_output=True, text=True)
        self.assertEqual((done.returncode, done.stdout), (0, ""))
