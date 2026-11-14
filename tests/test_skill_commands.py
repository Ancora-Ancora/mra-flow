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


if __name__ == "__main__":
    unittest.main()
