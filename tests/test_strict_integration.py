import importlib
import os
import shutil
import sys
import tempfile
import threading
import time
import unittest
from pathlib import Path

from sb3topy import config, main


class StrictIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp(prefix="sb3topy_strict_")
        self.output_dir = os.path.join(self.temp_dir, "out")
        self.project_path = "tests/minimal.sb3"
        if not os.path.exists(self.project_path):
            self.skipTest(f"Project file {self.project_path} not found.")

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def convert_project(self):
        config.restore_defaults()
        config.PROJECT_PATH = self.project_path
        config.OUTPUT_PATH = self.output_dir
        config.AUTORUN = False
        config.OVERWRITE_ENGINE = True
        config.RECONVERT_IMAGES = True

        result = main.run()
        self.assertTrue(result)

    def test_conversion_outputs_and_headless_quit(self):
        self.convert_project()

        output = Path(self.output_dir)
        project_file = output / "project.py"
        engine_dir = output / "engine"
        assets_dir = output / "assets"

        self.assertTrue(project_file.is_file())
        self.assertTrue((engine_dir / "runtime.py").is_file())
        self.assertTrue((engine_dir / "monitors.py").is_file())
        self.assertTrue(assets_dir.is_dir())

        code = project_file.read_text(encoding="utf-8")
        self.assertIn("from engine.monitors import Monitor, ListMonitor", code)
        self.assertIn("def setup_monitors(SPRITES):", code)
        self.assertIn("engine.start_program(setup_monitors)", code)
        self.assertNotIn("_clones: List['Target']", (engine_dir / "types" / "target.py").read_text(encoding="utf-8"))

        converted_svgs = list(assets_dir.glob("*-svg-2x.png"))
        self.assertGreater(len(converted_svgs), 0)

        old_cwd = os.getcwd()
        old_path = list(sys.path)
        old_env = {
            "SDL_VIDEODRIVER": os.environ.get("SDL_VIDEODRIVER"),
            "SDL_AUDIODRIVER": os.environ.get("SDL_AUDIODRIVER"),
        }

        try:
            os.environ["SDL_VIDEODRIVER"] = "dummy"
            os.environ["SDL_AUDIODRIVER"] = "dummy"
            os.chdir(self.output_dir)
            sys.path.insert(0, self.output_dir)

            for name in list(sys.modules):
                if name == "project" or name == "engine" or name.startswith("engine."):
                    del sys.modules[name]

            import pygame as pg
            project = importlib.import_module("project")

            def post_quit():
                time.sleep(0.5)
                pg.event.post(pg.event.Event(pg.QUIT))

            thread = threading.Thread(target=post_quit, daemon=True)
            thread.start()

            start = time.monotonic()
            project.engine.start_program(getattr(project, "setup_monitors", None))
            elapsed = time.monotonic() - start

            self.assertLess(elapsed, 4.0)

        finally:
            sys.path = old_path
            os.chdir(old_cwd)
            for key, value in old_env.items():
                if value is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = value
            for name in list(sys.modules):
                if name == "project" or name == "engine" or name.startswith("engine."):
                    del sys.modules[name]


if __name__ == "__main__":
    unittest.main()
