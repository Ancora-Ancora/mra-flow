import hashlib
import os

from installer import InstallError
from installer import reconcile as rc
from tests.support import TmpTestCase


class ReconcileTest(TmpTestCase):
    def setUp(self):
        super().setUp()
        self.payload = self.tmp / "payload"
        self.dest = self.tmp / "dest"
        self.payload.mkdir()
        self.dest.mkdir()

    def write(self, base, rel, text):
        p = base / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text)
        return p

    def kinds(self, manifest=None):
        return {a.path: a.kind for a in rc.plan(self.payload, self.dest, manifest)}

    def sha(self, text):
        return hashlib.sha256(text.encode()).hexdigest()

    def test_copy_new_file(self):
        self.write(self.payload, "a/x", "1")
        self.assertEqual(self.kinds(), {"a/x": rc.COPY})

    def test_skip_deleted_by_user(self):
        self.write(self.payload, "x", "1")
        self.assertEqual(self.kinds(rc.Manifest("0", {"x": self.sha("1")})), {"x": rc.SKIP_DELETED})

    def test_unmanaged_identical_is_adopted(self):
        self.write(self.payload, "x", "1")
        self.write(self.dest, "x", "1")
        self.assertEqual(self.kinds(), {"x": rc.ADOPT})

    def test_conflict_unmanaged_different(self):
        self.write(self.payload, "x", "1")
        self.write(self.dest, "x", "mine")
        self.assertEqual(self.kinds(), {"x": rc.CONFLICT})

    def test_unchanged(self):
        self.write(self.payload, "x", "1")
        self.write(self.dest, "x", "1")
        self.assertEqual(self.kinds(rc.Manifest("0", {"x": self.sha("1")})), {"x": rc.UNCHANGED})

    def test_copy_update_unedited(self):
        self.write(self.payload, "x", "2")
        self.write(self.dest, "x", "1")
        self.assertEqual(self.kinds(rc.Manifest("0", {"x": self.sha("1")})), {"x": rc.COPY})

    def test_adopt_edit_matching_new_payload(self):
        self.write(self.payload, "x", "2")
        self.write(self.dest, "x", "2")
        self.assertEqual(self.kinds(rc.Manifest("0", {"x": self.sha("1")})), {"x": rc.ADOPT})

    def test_skip_local_edit(self):
        self.write(self.payload, "x", "2")
        self.write(self.dest, "x", "mine")
        self.assertEqual(self.kinds(rc.Manifest("0", {"x": self.sha("1")})), {"x": rc.SKIP_LOCAL_EDIT})

    def test_delete_dropped_unedited(self):
        self.write(self.dest, "d/x", "1")
        m = rc.Manifest("0", {"d/x": self.sha("1")})
        actions = rc.plan(self.payload, self.dest, m)
        self.assertEqual([a.kind for a in actions], [rc.DELETE])
        new = rc.apply(actions, self.payload, self.dest, "0.2", m)
        self.assertFalse((self.dest / "d").exists())
        self.assertEqual(new.files, {})

    def test_keep_orphan_edited(self):
        self.write(self.dest, "x", "mine")
        self.assertEqual(self.kinds(rc.Manifest("0", {"x": self.sha("1")})), {"x": rc.KEEP_ORPHAN})

    def test_forget_dropped_and_gone(self):
        self.assertEqual(self.kinds(rc.Manifest("0", {"x": self.sha("1")})), {"x": rc.FORGET})

    def test_apply_round_trip_and_flag_kept(self):
        self.write(self.payload, "a", "1")
        self.write(self.payload, "b", "1")
        exe = self.write(self.payload, "bin/tool", "#!/bin/sh\n")
        os.chmod(exe, 0o755)
        new = rc.apply(rc.plan(self.payload, self.dest, None), self.payload, self.dest, "0.1", None)
        self.assertTrue(os.access(self.dest / "bin/tool", os.X_OK))
        self.assertEqual(set(self.kinds(new).values()), {rc.UNCHANGED})
        # local edit, then a new payload: the edit stays flagged across updates
        self.write(self.dest, "a", "mine")
        self.write(self.payload, "a", "2")
        new2 = rc.apply(rc.plan(self.payload, self.dest, new), self.payload, self.dest, "0.2", new)
        self.assertEqual((self.dest / "a").read_text(), "mine")
        self.assertEqual(self.kinds(new2)["a"], rc.SKIP_LOCAL_EDIT)

    def test_apply_refuses_conflicts(self):
        with self.assertRaises(InstallError):
            rc.apply([rc.Action(rc.CONFLICT, "x")], self.payload, self.dest, "0", None)

    def test_manifest_save_load_and_invalid(self):
        rc.save_manifest(self.dest, rc.Manifest("0.3.0", {"x": "abc"}))
        self.assertEqual(rc.load_manifest(self.dest), rc.Manifest("0.3.0", {"x": "abc"}))
        self.assertEqual((self.dest / rc.VERSION_PATH).read_text(), "0.3.0\n")
        (self.dest / rc.MANIFEST_PATH).write_text("{oops")
        with self.assertRaises(InstallError):
            rc.load_manifest(self.dest)
