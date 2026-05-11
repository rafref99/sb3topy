import tkinter as tk
import tempfile
import unittest

from sb3topy.gui.convert import ConvertFrame


class _Var:
    def __init__(self, value=""):
        self.value = value

    def get(self):
        return self.value

    def set(self, value):
        self.value = value


class _FakeApp:
    def __init__(self):
        self.vars = {}
        self.wrote_config = False
        self.ran_main = False

    def setvar(self, name, value):
        self.vars[name] = value

    def write_config(self):
        self.wrote_config = True

    def run_main(self):
        self.ran_main = True


class ConvertDragDropTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tcl = tk.Tcl()

    def test_drop_paths_parses_braced_paths_with_spaces(self):
        paths = ConvertFrame.drop_paths(
            "{/tmp/My Project.sb3} {/tmp/Other Project.zip}",
            self.tcl.splitlist,
        )

        self.assertEqual(paths, [
            "/tmp/My Project.sb3",
            "/tmp/Other Project.zip",
        ])

    def test_choose_project_path_prefers_first_supported_project_file(self):
        project_path = ConvertFrame.choose_project_path([
            "/tmp/readme.txt",
            "/tmp/game.SB3",
            "/tmp/archive.zip",
        ])

        self.assertEqual(project_path, "/tmp/game.SB3")

    def test_choose_project_path_ignores_unsupported_files(self):
        project_path = ConvertFrame.choose_project_path([
            "/tmp/image.png",
            "/tmp/notes.txt",
        ])

        self.assertEqual(project_path, "")

    def test_choose_project_path_accepts_directory(self):
        with tempfile.TemporaryDirectory() as project_dir:
            project_path = ConvertFrame.choose_project_path([
                "/tmp/readme.txt",
                project_dir,
            ])

        self.assertEqual(project_path, project_dir)

    def test_set_project_url_clears_local_source(self):
        frame = ConvertFrame.__new__(ConvertFrame)
        frame.app = _FakeApp()
        frame.source_mode = _Var()

        frame.set_project_url(" https://scratch.mit.edu/projects/123/ ")

        self.assertEqual(frame.source_mode.get(), "URL")
        self.assertEqual(frame.app.vars["PROJECT_URL"], "https://scratch.mit.edu/projects/123/")
        self.assertEqual(frame.app.vars["PROJECT_PATH"], "")
        self.assertFalse(frame.app.vars["JSON_SHA"])

    def test_convert_uses_url_source(self):
        frame = ConvertFrame.__new__(ConvertFrame)
        frame.app = _FakeApp()
        frame.source_mode = _Var("URL")
        frame.project_url = _Var("https://scratch.mit.edu/projects/123/")
        frame.project_path = _Var("/tmp/local.sb3")

        frame.convert()

        self.assertEqual(frame.app.vars["PROJECT_URL"], "https://scratch.mit.edu/projects/123/")
        self.assertEqual(frame.app.vars["PROJECT_PATH"], "")
        self.assertTrue(frame.app.vars["AUTORUN"])
        self.assertTrue(frame.app.vars["PARSE_PROJECT"])
        self.assertTrue(frame.app.vars["COPY_ENGINE"])
        self.assertTrue(frame.app.wrote_config)
        self.assertTrue(frame.app.ran_main)

    def test_convert_uses_directory_source(self):
        frame = ConvertFrame.__new__(ConvertFrame)
        frame.app = _FakeApp()
        frame.source_mode = _Var("Directory")
        frame.project_url = _Var("https://scratch.mit.edu/projects/123/")
        frame.project_path = _Var("/tmp/project-dir")

        frame.convert()

        self.assertEqual(frame.app.vars["PROJECT_PATH"], "/tmp/project-dir")
        self.assertEqual(frame.app.vars["PROJECT_URL"], "")


if __name__ == "__main__":
    unittest.main()
