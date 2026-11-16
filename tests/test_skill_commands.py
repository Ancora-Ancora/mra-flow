import re
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


if __name__ == "__main__":
    unittest.main()
