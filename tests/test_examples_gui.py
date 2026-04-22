import os
import tempfile
import unittest
from unittest import mock

from sb3topy.gui.examples import Example, ExamplesFrame


class ExamplesGuiTests(unittest.TestCase):
    def make_example(self):
        return Example({
            "name": "Demo Project!",
            "id": 12345,
            "link": "https://scratch.mit.edu/projects/12345/",
            "author": "tester",
            "description": "Demo\nDetails",
            "sha256": "",
            "config": {},
        })

    def test_example_download_detection_requires_project_and_engine(self):
        example = self.make_example()

        with tempfile.TemporaryDirectory() as temp_dir:
            with mock.patch("sb3topy.gui.examples.path.expanduser", return_value=temp_dir):
                with mock.patch.object(ExamplesFrame, "update_action_buttons", lambda self: None):
                    frame = object.__new__(ExamplesFrame)
                    frame.example = example

                    output_path = frame.example_output_path()
                    self.assertTrue(output_path.endswith("DemoProject_12345"))
                    self.assertFalse(frame.example_is_downloaded())

                    os.makedirs(os.path.join(output_path, "engine"))
                    with open(os.path.join(output_path, "project.py"), "w", encoding="utf-8") as project_file:
                        project_file.write("")
                    self.assertFalse(frame.example_is_downloaded())

                    with open(os.path.join(output_path, "engine", "runtime.py"), "w", encoding="utf-8") as runtime_file:
                        runtime_file.write("")
                    self.assertTrue(frame.example_is_downloaded())


if __name__ == "__main__":
    unittest.main()
