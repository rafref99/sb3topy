import unittest
import os
import shutil
from sb3topy import main

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

if __name__ == '__main__':
    unittest.main()
