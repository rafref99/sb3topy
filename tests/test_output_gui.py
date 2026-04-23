import queue
import unittest

from sb3topy.gui.output import OutputFrame


class _FakeTextbox:
    def __init__(self):
        self.content = ""

    def configure(self, **_kwargs):
        pass

    def insert(self, _index, text):
        self.content += text

    def see(self, _index):
        pass


class _FakeVar:
    def __init__(self):
        self.value = None

    def set(self, value):
        self.value = value


class _DeadProcess:
    exitcode = 7

    @staticmethod
    def is_alive():
        return False


class OutputGuiTests(unittest.TestCase):
    def test_unexpected_log_end_reports_worker_exit_code(self):
        frame = object.__new__(OutputFrame)
        frame.text = _FakeTextbox()
        frame.status = _FakeVar()
        frame.queue = queue.Queue()
        frame.process = _DeadProcess()
        frame.finished = False
        frame.dead_polls = 39
        frame.after = lambda *_args, **_kwargs: None

        frame.update_loop()

        self.assertIn("Worker exit code: 7", frame.text.content)
        self.assertEqual(frame.status.value, "Worker exited unexpectedly (7)")
        self.assertTrue(frame.finished)


if __name__ == "__main__":
    unittest.main()
