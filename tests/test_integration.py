import unittest
import os
import shutil
import tempfile
import zipfile
from sb3topy import main, project as project_helpers, unpacker

class IntegrationTests(unittest.TestCase):
    def setUp(self):
        self.output_dir = "test_output"
        if os.path.exists(self.output_dir):
            shutil.rmtree(self.output_dir)

    def tearDown(self):
        if os.path.exists(self.output_dir):
            shutil.rmtree(self.output_dir)

    def test_minimal_project_conversion(self):
        # This test requires a minimal .sb3 file. 
        # Since we don't have one, we can only mock the process or skip it if file missing.
        project_path = "tests/minimal.sb3"
        if not os.path.exists(project_path):
            self.skipTest(f"Project file {project_path} not found.")
        
        # Test conversion
        result = main.main(['sb3topy', project_path, self.output_dir])
        self.assertTrue(result)
        self.assertTrue(os.path.exists(os.path.join(self.output_dir, "project.py")))

    def test_extract_project_from_directory(self):
        project_path = "tests/minimal.sb3"
        if not os.path.exists(project_path):
            self.skipTest(f"Project file {project_path} not found.")

        with tempfile.TemporaryDirectory() as source_dir, tempfile.TemporaryDirectory() as output_dir:
            with zipfile.ZipFile(project_path) as project_zip:
                project_zip.extractall(source_dir)

            manifest = project_helpers.Manifest(output_dir)
            sb3 = unpacker.extract_project(manifest, source_dir)

            self.assertTrue(sb3.is_sb3())
            self.assertTrue(os.path.isdir(os.path.join(output_dir, "assets")))

if __name__ == '__main__':
    unittest.main()
