"""The bin/ wrapper.

Two things matter and both have bitten this repo before: the script must be
committed executable, so nobody is told to chmod it, and it must resolve its
own location rather than trusting cwd, so it works from anywhere.
"""

import os
import subprocess
import unittest

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
WRAPPER = os.path.join(REPO, "bin", "audit-agent-conversation")


class TestWrapper(unittest.TestCase):
    def test_wrapper_exists(self):
        self.assertTrue(os.path.isfile(WRAPPER), WRAPPER)

    def test_wrapper_is_executable(self):
        """"Make executables actually executable; don't tell users to chmod."""
        self.assertTrue(os.access(WRAPPER, os.X_OK), "%s is not executable" % WRAPPER)

    def test_committed_with_mode_755(self):
        out = subprocess.check_output(
            ["git", "ls-files", "-s", "bin/audit-agent-conversation"], cwd=REPO
        ).decode()
        self.assertTrue(out.startswith("100755"), out.strip() or "not tracked")

    def test_help_runs_and_exits_zero(self):
        process = subprocess.Popen(
            [WRAPPER, "--help"], stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        stdout, stderr = process.communicate()
        self.assertEqual(process.returncode, 0, stderr.decode())
        self.assertIn("audit-agent-conversation", stdout.decode())

    def test_works_from_an_unrelated_working_directory(self):
        """Resolves its own location, not cwd."""
        process = subprocess.Popen(
            [WRAPPER, "--help"], cwd="/", stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        stdout, stderr = process.communicate()
        self.assertEqual(process.returncode, 0, stderr.decode())

    def test_refusal_exit_code_survives_the_wrapper(self):
        """`exec` must not swallow the CLI's exit status."""
        from tests import fixtures

        fixtures.require_corpus(self)
        process = subprocess.Popen(
            [WRAPPER, fixtures.path(fixtures.MULTITURN_SMALL), "--stdout"],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        )
        stdout, stderr = process.communicate()
        self.assertEqual(process.returncode, 3)
        self.assertIn(b"user turns", stderr)



class TestWrapperThroughASymlink(unittest.TestCase):
    """Its real-world shape. The dotfiles install links bin/ into $HOME, so in
    normal use this script IS a symlink and must still find the skill package.
    """

    def _run_via(self, link, *args):
        return subprocess.Popen(
            [link] + list(args), stdout=subprocess.PIPE, stderr=subprocess.PIPE
        ).communicate()

    def test_absolute_symlink(self):
        import os
        import shutil
        import tempfile

        tmp = tempfile.mkdtemp(prefix="auditlog-link-")
        try:
            link = os.path.join(tmp, "audit-agent-conversation")
            os.symlink(WRAPPER, link)
            stdout, stderr = self._run_via(link, "--help")
            self.assertIn(b"audit-agent-conversation", stdout, stderr.decode())
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_chained_symlinks(self):
        import os
        import shutil
        import tempfile

        tmp = tempfile.mkdtemp(prefix="auditlog-chain-")
        try:
            first = os.path.join(tmp, "one")
            second = os.path.join(tmp, "two")
            os.symlink(WRAPPER, first)
            os.symlink(first, second)
            stdout, stderr = self._run_via(second, "--help")
            self.assertIn(b"audit-agent-conversation", stdout, stderr.decode())
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_relative_symlink(self):
        import os
        import shutil
        import tempfile

        # realpath, because macOS /var is itself a symlink to /private/var and
        # a relpath computed from the logical path does not resolve.
        tmp = os.path.realpath(tempfile.mkdtemp(prefix="auditlog-rel-"))
        try:
            link = os.path.join(tmp, "audit-agent-conversation")
            os.symlink(os.path.relpath(os.path.realpath(WRAPPER), tmp), link)
            stdout, stderr = self._run_via(link, "--help")
            self.assertIn(b"audit-agent-conversation", stdout, stderr.decode())
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

if __name__ == "__main__":
    unittest.main()
