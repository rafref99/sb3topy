import tkinter as tk
import unittest

from sb3topy.gui.convert import ConvertFrame


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


if __name__ == "__main__":
    unittest.main()
