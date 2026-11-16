import json

from installer import InstallError
from installer import shared_files as sf
from tests.support import TmpTestCase


class ClaudeImportTest(TmpTestCase):
    def test_created_when_missing(self):
        self.assertTrue(sf.ensure_claude_import(self.tmp))
        self.assertEqual((self.tmp / "CLAUDE.md").read_text(), sf.IMPORT_LINE + "\n")

    def test_added_once_keeping_content(self):
        (self.tmp / "CLAUDE.md").write_text("# Project\nno newline")
        self.assertTrue(sf.ensure_claude_import(self.tmp))
        self.assertFalse(sf.ensure_claude_import(self.tmp))
        text = (self.tmp / "CLAUDE.md").read_text()
        self.assertTrue(text.startswith("# Project\nno newline\n"))
        self.assertEqual(text.count(sf.IMPORT_LINE), 1)


class SettingsTest(TmpTestCase):
    def setUp(self):
        super().setUp()
        self.hook = sf.hook_entry(self.tmp)

    def path(self):
        return self.tmp / "settings.json"

    def write(self, data):
        self.path().write_text(data if isinstance(data, str) else json.dumps(data))

    def load(self):
        return json.loads(self.path().read_text())

    def merge(self):
        return sf.merge_settings(self.path(), hook=self.hook, plugins=sf.REQUIRED_PLUGINS)

    def test_hook_command_is_absolute(self):
        self.assertEqual(self.hook["hooks"][0]["command"],
                         f'python3 "{self.tmp}/mra-flow/hooks/load-handoff.py"')

    def test_keeps_other_hooks_and_keys(self):
        bd = {"matcher": "", "hooks": [{"type": "command", "command": "bd prime --hook-json"}]}
        self.write({"permissions": {"allow": ["Bash(ls)"]}, "hooks": {"SessionStart": [bd]}})
        self.assertTrue(self.merge())
        s = self.load()
        self.assertEqual(s["permissions"], {"allow": ["Bash(ls)"]})
        self.assertEqual(s["hooks"]["SessionStart"], [bd, self.hook])
        self.assertEqual(s["enabledPlugins"], {p: True for p in sf.REQUIRED_PLUGINS})

    def test_replaces_stale_hook_once(self):
        stale = {"matcher": "startup", "hooks": [
            {"type": "command", "command": "python3 /old/place/mra-flow/hooks/load-handoff.py"}]}
        self.write({"hooks": {"SessionStart": [stale, dict(stale)]}})
        self.merge()
        self.assertEqual(self.load()["hooks"]["SessionStart"], [self.hook])

    def test_two_different_hooks_coexist(self):
        drift = sf.drift_hook_entry(self.tmp)
        self.merge()
        sf.merge_settings(self.path(), hook=drift)
        self.assertEqual(self.load()["hooks"]["SessionStart"], [self.hook, drift])
        # re-merging the first hook leaves the second alone
        sf.merge_settings(self.path(), hook=self.hook)
        self.assertEqual(self.load()["hooks"]["SessionStart"], [self.hook, drift])

    def test_plugins_only_adds_no_hooks(self):
        sf.merge_settings(self.path(), plugins=sf.REQUIRED_PLUGINS)
        self.assertNotIn("hooks", self.load())

    def test_keeps_plugin_false(self):
        self.write({"enabledPlugins": {sf.REQUIRED_PLUGINS[0]: False}})
        self.merge()
        self.assertEqual(self.load()["enabledPlugins"],
                         {sf.REQUIRED_PLUGINS[0]: False, sf.REQUIRED_PLUGINS[1]: True})

    def test_idempotent(self):
        self.assertTrue(self.merge())
        before = self.path().read_bytes()
        self.assertFalse(self.merge())
        self.assertEqual(self.path().read_bytes(), before)

    def test_invalid_settings_raises_and_leaves_file(self):
        self.write('{"hooks": {},}')
        with self.assertRaises(InstallError):
            self.merge()
        self.assertEqual(self.path().read_text(), '{"hooks": {},}')


class GitignoreTest(TmpTestCase):
    def test_appends_missing_only(self):
        (self.tmp / ".gitignore").write_text("node_modules/\n.worktrees/")
        self.assertTrue(sf.ensure_gitignore(self.tmp))
        self.assertFalse(sf.ensure_gitignore(self.tmp))
        lines = (self.tmp / ".gitignore").read_text().splitlines()
        self.assertEqual(lines.count(".worktrees/"), 1)
        self.assertIn("handoff/", lines)
        self.assertIn(".beads/issues.jsonl", lines)
        self.assertEqual(lines[0], "node_modules/")
