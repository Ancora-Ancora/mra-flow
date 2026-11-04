import shutil
import subprocess
import sys
import tomllib

from installer.environment import REGISTRY_SKELETON
from tests.support import REPO_ROOT, TmpTestCase, git, make_bare_remote, make_orchestrator

SCRIPT = REPO_ROOT / "payload" / "orchestrator" / ".mra-flow" / "bin" / "mra-repo"


class MraRepoTest(TmpTestCase):
    def setUp(self):
        super().setUp()
        self.orch = make_orchestrator(self.tmp)
        (self.orch / ".mra-flow/bin").mkdir(parents=True)
        shutil.copy2(SCRIPT, self.orch / ".mra-flow/bin/mra-repo")
        (self.orch / "mra-flow.toml").write_text(REGISTRY_SKELETON)
        self.be = make_bare_remote(self.tmp, "proj-be")
        self.fe = make_bare_remote(self.tmp, "proj-fe")

    def run_repo(self, *args):
        return subprocess.run([sys.executable, str(self.orch / ".mra-flow/bin/mra-repo"), *args],
                              capture_output=True, text=True)

    def registry(self):
        return tomllib.loads((self.orch / "mra-flow.toml").read_text())["repos"]

    def files(self):
        return {n: (self.orch / n).read_bytes() if (self.orch / n).exists() else None
                for n in ("mra-flow.toml", ".gitignore")}

    def add_be_fe(self):
        self.assertEqual(self.run_repo("add", "be", str(self.be), "--description", "Backend").returncode, 0)
        done = self.run_repo("add", "fe", str(self.fe), "--description", 'SPA "web"', "--depends-on", "be")
        self.assertEqual(done.returncode, 0, done.stderr)

    def test_add_clones_and_declares(self):
        self.add_be_fe()
        self.assertEqual(self.registry(), {
            "be": {"path": "proj-be", "remote": str(self.be), "description": "Backend", "depends_on": []},
            "fe": {"path": "proj-fe", "remote": str(self.fe), "description": 'SPA "web"', "depends_on": ["be"]},
        })
        self.assertTrue((self.orch / "proj-be/.git").is_dir())
        lines = (self.orch / ".gitignore").read_text().splitlines()
        self.assertIn("/proj-be/", lines)
        self.assertIn("/proj-fe/", lines)
        self.assertIn("# mra-flow repo registry", (self.orch / "mra-flow.toml").read_text())

    def test_add_custom_path(self):
        done = self.run_repo("add", "api", str(self.be), "--description", "x", "--path", "api")
        self.assertEqual(done.returncode, 0, done.stderr)
        self.assertEqual(self.registry()["api"]["path"], "api")

    def test_add_refusals_change_nothing(self):
        self.add_be_fe()
        before = self.files()
        for args in (("be", str(self.be), "--description", "dup"),
                     ("x", str(self.be), "--description", "d", "--depends-on", "nope"),
                     ("Be", str(self.be), "--description", "bad key"),
                     ("other", "/nonexistent.git", "--description", "bad remote")):
            done = self.run_repo("add", *args)
            self.assertEqual(done.returncode, 1, args)
            self.assertIn("Error:", done.stderr)
            self.assertEqual(self.files(), before, args)
        self.assertFalse((self.orch / "nonexistent").exists())

    def test_clone_recreates_missing(self):
        self.add_be_fe()
        shutil.rmtree(self.orch / "proj-fe")
        done = self.run_repo("clone")
        self.assertEqual(done.returncode, 0, done.stderr)
        self.assertEqual(done.stdout.splitlines(), ["be: present", "fe: cloned"])
        self.assertTrue((self.orch / "proj-fe/.git").is_dir())
        self.assertEqual(git(self.orch, "config", "beads.role"), "maintainer")

    def test_list_topological(self):
        self.add_be_fe()
        done = self.run_repo("add", "docs", str(self.be), "--description", "d", "--path", "docs")
        self.assertEqual(done.returncode, 0, done.stderr)
        out = self.run_repo("list").stdout.splitlines()
        self.assertEqual(out, ["be\tproj-be\t", "docs\tdocs\t", "fe\tproj-fe\tbe"])

    def test_list_cycle_fails(self):
        with open(self.orch / "mra-flow.toml", "a") as f:
            for k, dep in (("a", "b"), ("b", "a")):
                f.write(f'[repos.{k}]\npath = "{k}"\nremote = "r"\ndescription = "d"\ndepends_on = ["{dep}"]\n')
        done = self.run_repo("list")
        self.assertEqual(done.returncode, 1)
        self.assertIn("cycle among: a, b", done.stderr)
