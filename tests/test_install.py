import json
import os
import subprocess
import shutil
import tomllib

from installer import environment as env
from installer import reconcile as rc
from installer import shared_files as sf
from tests.support import (TmpTestCase, calls, fake_env, git, make_orchestrator,
                           make_package, run_install, snapshot)

SKILL = ".claude/skills/mra-build/SKILL.md"
MRA_REPO = ".mra-flow/bin/mra-repo"


class InstallTest(TmpTestCase):
    def setUp(self):
        super().setUp()
        self.pkg = make_package(self.tmp)
        self.orch = make_orchestrator(self.tmp)
        self.env = fake_env(self.tmp)

    def install(self, **env_overrides):
        done = run_install(self.pkg, self.orch, {**self.env, **env_overrides})
        return done

    def ok(self):
        done = self.install()
        self.assertEqual(done.returncode, 0, done.stdout + done.stderr)
        return done

    def bump(self, version, rel=SKILL, text="new upstream text\n"):
        (self.pkg / "VERSION").write_text(version + "\n")
        (self.pkg / "payload" / "orchestrator" / rel).write_text(text)

    def test_fresh_install(self):
        self.ok()
        payload = rc.payload_files(self.pkg / "payload" / "orchestrator")
        for rel in payload:
            self.assertTrue((self.orch / rel).is_file(), rel)
        manifest = rc.load_manifest(self.orch)
        self.assertEqual(manifest.version, "0.1.0")
        self.assertEqual(manifest.files, payload)
        self.assertIn(sf.IMPORT_LINE, (self.orch / "CLAUDE.md").read_text())
        settings = json.loads((self.orch / ".claude/settings.json").read_text())
        self.assertEqual(settings, {
            "enabledPlugins": {p: True for p in sf.REQUIRED_PLUGINS},
            "hooks": {"SessionStart": [sf.drift_hook_entry(self.orch), sf.update_hook_entry(self.orch)]},
        })
        self.assertFalse((self.orch / "mra-flow/hooks").exists())
        self.assertTrue((self.orch / sf.DRIFT_HOOK_SCRIPT).is_file())
        self.assertTrue((self.orch / sf.UPDATE_HOOK_SCRIPT).is_file())
        self.assertIn(".mra-flow/update-state.json", (self.orch / ".gitignore").read_text())
        self.assertEqual(tomllib.loads((self.orch / "mra-flow.toml").read_text()), {})
        self.assertIn("schema: mra-flow", (self.orch / "openspec/config.yaml").read_text())
        self.assertEqual(git(self.orch, "config", "beads.role"), "maintainer")
        self.assertIn("bd init --skip-agents", calls(self.tmp))

    def test_reinstall_is_noop(self):
        self.ok()
        before = snapshot(self.orch)
        out = self.ok().stdout
        self.assertEqual(snapshot(self.orch), before)
        self.assertRegex(out, r"files: unchanged \d+\n")

    def test_update_without_local_edits(self):
        self.ok()
        self.bump("0.2.0")
        out = self.ok().stdout
        self.assertIn("updated from 0.1.0", out)
        self.assertEqual((self.orch / SKILL).read_text(), "new upstream text\n")
        self.assertEqual(rc.load_manifest(self.orch).version, "0.2.0")

    def test_update_keeps_local_edit(self):
        self.ok()
        (self.orch / SKILL).write_text("my edit\n")
        self.bump("0.2.0")
        other = ".claude/skills/mra-fix/SKILL.md"
        (self.pkg / "payload" / "orchestrator" / other).write_text("fix v2\n")
        out = self.ok().stdout
        self.assertEqual((self.orch / SKILL).read_text(), "my edit\n")
        self.assertIn(f"left alone (skip-local-edit): {SKILL}", out)
        self.assertEqual((self.orch / other).read_text(), "fix v2\n")

    def test_unmanaged_file_refuses_untouched(self):
        (self.orch / SKILL).parent.mkdir(parents=True)
        (self.orch / SKILL).write_text("pre-package copy\n")
        before = snapshot(self.orch)
        done = self.install()
        self.assertEqual(done.returncode, 1)
        self.assertIn(SKILL, done.stdout)
        self.assertEqual(snapshot(self.orch), before)

    def test_active_change_warns(self):
        self.ok()
        (self.orch / "openspec/changes/foo").mkdir(parents=True)
        (self.orch / "openspec/changes/archive").mkdir()
        (self.orch / ".worktrees/foo").mkdir(parents=True)
        out = self.ok().stdout
        self.assertIn("warning: OpenSpec change in flight: foo", out)
        self.assertIn("warning: worktree in flight: .worktrees/foo", out)
        self.assertNotIn("in flight: archive", out)

    def test_update_points_existing_changes_to_roadmap_retro_until_it_exists(self):
        self.ok()
        (self.orch / "openspec/changes/archive/2026-01-01-foo").mkdir(parents=True)
        self.assertIn("/mra-roadmap --retro", self.ok().stdout)
        self.assertIn("/mra-roadmap --retro", self.ok().stdout)  # every update, until the roadmap exists
        (self.orch / "docs/roadmap").mkdir(parents=True)
        self.assertIn("/mra-roadmap --retro", self.ok().stdout)  # an empty folder is no roadmap
        (self.orch / f"docs/roadmap/{self.orch.name}.md").write_text("| Estimate (h) |\n")
        self.assertNotIn("/mra-roadmap", self.ok().stdout)

    def test_no_roadmap_note_without_changes(self):
        self.ok()
        self.assertNotIn("--retro", self.ok().stdout)

    def test_update_points_other_and_day_roadmaps_to_the_project_initiative(self):
        self.ok()
        roadmaps = self.orch / "docs/roadmap"
        roadmaps.mkdir(parents=True)
        (roadmaps / f"{self.orch.name}.md").write_text("| Estimate (h) |\n")
        (roadmaps / f"{self.orch.name}-effort.md").write_text("generated\n")
        self.assertNotIn("/mra-roadmap", self.ok().stdout)
        (roadmaps / "go-live.md").write_text("| Estimate (h) |\n")
        self.assertIn(f"docs/roadmap/go-live.md is not the project's one roadmap: merge it with `/mra-roadmap {self.orch.name}`", self.ok().stdout)
        (roadmaps / "go-live.md").unlink()
        (roadmaps / f"{self.orch.name}.md").write_text("| Estimate (d) |\n")
        self.assertIn(f"is in days: convert it with `/mra-roadmap {self.orch.name}`", self.ok().stdout)

    def test_openspec_gate(self):
        before = snapshot(self.orch)
        done = self.install(FAKE_OPENSPEC_VERSION="1.15.9")
        self.assertEqual(done.returncode, 1)
        self.assertIn("older than the required 1.16.0", done.stderr)
        self.assertEqual(snapshot(self.orch), before)
        done = self.install(FAKE_OPENSPEC_VERSION="1.17.0")
        self.assertEqual(done.returncode, 0, done.stderr)
        self.assertIn("newer than the tested 1.16.0", done.stdout)

    def test_missing_openspec_skills_refuse(self):
        done = self.install(FAKE_OPENSPEC_SKIP_SKILLS="1")
        self.assertEqual(done.returncode, 1)
        self.assertIn("openspec-explore", done.stderr)
        self.assertFalse((self.orch / rc.MANIFEST_PATH).exists())

    def test_executables_keep_mode(self):
        self.ok()
        self.assertTrue(os.access(self.orch / MRA_REPO, os.X_OK))
        self.bump("0.2.0", rel=MRA_REPO, text="#!/usr/bin/env python3\nprint('v2')\n")
        self.ok()
        self.assertTrue(os.access(self.orch / MRA_REPO, os.X_OK))

    def test_target_must_be_git_toplevel(self):
        sub = self.orch / "sub"
        sub.mkdir()
        for target in (self.tmp / "missing", sub, self.tmp):
            done = run_install(self.pkg, target, self.env)
            self.assertEqual(done.returncode, 1, target)
            self.assertIn("Error:", done.stderr)

    def test_existing_openspec_config_gets_schema(self):
        (self.orch / "openspec").mkdir()
        (self.orch / "openspec/config.yaml").write_text("context: |\n  keep me\n")
        for name in env.REQUIRED_OPENSPEC_SKILLS:
            (self.orch / ".claude/skills" / name).mkdir(parents=True)
            (self.orch / ".claude/skills" / name / "SKILL.md").write_text(name)
        self.ok()
        text = (self.orch / "openspec/config.yaml").read_text()
        self.assertTrue(text.startswith("schema: mra-flow\n"))
        self.assertIn("keep me", text)
        self.assertNotIn("openspec init --tools claude .", calls(self.tmp))


class InstallShTest(TmpTestCase):
    """install.sh, including --update against a cache cloned from a bare repo with tags."""

    def setUp(self):
        super().setUp()
        self.env = fake_env(self.tmp)
        self.orch = make_orchestrator(self.tmp)
        src = make_package(self.tmp)
        git(src, "init", "--quiet", "-b", "main")
        git(src, "config", "user.name", "T")
        git(src, "config", "user.email", "t@example.com")
        git(src, "add", "-A")
        git(src, "commit", "--quiet", "-m", "v0.1.0")
        git(src, "tag", "v0.1.0")
        (src / "VERSION").write_text("0.2.0\n")
        (src / "payload" / "orchestrator" / SKILL).write_text("v2\n")
        git(src, "commit", "--quiet", "-am", "v0.2.0")
        git(src, "tag", "v0.2.0")
        self.cache = self.tmp / "cache"
        git(self.tmp, "clone", "--quiet", str(src), str(self.cache))
        git(self.cache, "-c", "advice.detachedHead=false", "checkout", "--quiet", "v0.1.0")

    def sh(self, *args):
        return subprocess.run(["bash", str(self.cache / "install.sh"), *args],
                              env=self.env, capture_output=True, text=True)

    def test_install_then_update_to_latest_and_back(self):
        done = self.sh(str(self.orch))
        self.assertEqual(done.returncode, 0, done.stderr)
        self.assertEqual(rc.load_manifest(self.orch).version, "0.1.0")
        done = self.sh("--update", str(self.orch))
        self.assertEqual(done.returncode, 0, done.stderr)
        self.assertEqual(rc.load_manifest(self.orch).version, "0.2.0")
        self.assertEqual((self.orch / SKILL).read_text(), "v2\n")
        self.assertEqual(git(self.cache, "describe", "--tags"), "v0.2.0")
        done = self.sh("--update", "v0.1.0", str(self.orch))
        self.assertEqual(done.returncode, 0, done.stderr)
        self.assertEqual(rc.load_manifest(self.orch).version, "0.1.0")

    def test_update_refuses_dirty_cache(self):
        self.sh(str(self.orch))
        (self.cache / "stray").write_text("x")
        before = snapshot(self.orch)
        done = self.sh("--update", str(self.orch))
        self.assertEqual(done.returncode, 1)
        self.assertIn("local changes", done.stderr)
        self.assertEqual(snapshot(self.orch), before)

    def test_usage(self):
        self.assertEqual(self.sh().returncode, 1)
