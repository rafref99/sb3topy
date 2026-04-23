import unittest
import pickle
from unittest import mock

from sb3topy import config
from sb3topy import main


class ConfigIsolationTests(unittest.TestCase):
    def setUp(self):
        self.old_config = config.get_config()

    def tearDown(self):
        config.set_config(self.old_config)

    def test_parse_args_clears_stale_project_url(self):
        config.PROJECT_URL = "https://scratch.mit.edu/projects/123/"
        config.AUTORUN = True

        config.parse_args(["sb3topy", "tests/minimal.sb3", "out"])

        self.assertEqual(config.PROJECT_URL, "")
        self.assertEqual(config.PROJECT_PATH, "tests/minimal.sb3")
        self.assertEqual(config.OUTPUT_PATH, "out")
        self.assertFalse(config.AUTORUN)

    def test_repeated_parse_args_does_not_reuse_autorun(self):
        config.parse_args(["sb3topy", "-r", "first.sb3", "out1"])
        self.assertTrue(config.AUTORUN)

        config.parse_args(["sb3topy", "second.sb3", "out2"])

        self.assertFalse(config.AUTORUN)
        self.assertEqual(config.PROJECT_PATH, "second.sb3")
        self.assertEqual(config.OUTPUT_PATH, "out2")

    def test_config_snapshot_round_trips_through_pickle(self):
        config.restore_defaults()
        config.PROJECT_PATH = "tests/minimal.sb3"

        snapshot = config.snapshot_config()
        restored = pickle.loads(pickle.dumps(snapshot))

        self.assertEqual(restored.PROJECT_PATH, "tests/minimal.sb3")
        self.assertEqual(restored.BLANK_SVG_HASHES, config.BLANK_SVG_HASHES)

    def test_run_uses_snapshot_for_autorun(self):
        config.restore_defaults()
        config.PROJECT_PATH = "tests/minimal.sb3"
        config.OUTPUT_PATH = ""
        config.AUTORUN = False
        run_config = config.snapshot_config()

        config.AUTORUN = True

        with mock.patch("sb3topy.packer.packer.run_project") as run_project:
            result = main.run(run_config)

        self.assertTrue(result)
        run_project.assert_not_called()


if __name__ == "__main__":
    unittest.main()
