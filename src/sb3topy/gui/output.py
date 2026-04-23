"""
output.py

Contains the Output tab of the GUI
"""

import tkinter as tk
import customtkinter as ctk

import queue
import logging

from . import style


class OutputFrame(ctk.CTkFrame):
    """Handles the Output tab, logging"""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs, fg_color=style.APP_BG)

        self.app = parent

        self.process = None
        self.queue = None
        self.finished = False
        self.dead_polls = 0

        header = style.page_header(
            self, "Output",
            "Conversion progress and runtime launch messages appear here.")

        log_frame = style.section(self, "Log")
        self.status = ctk.StringVar(value="Idle")
        status_label = ctk.CTkLabel(
            log_frame, textvariable=self.status, text_color=style.MUTED,
            anchor="e")

        self.text = ctk.CTkTextbox(
            log_frame, width=32, height=17.5, state="disabled",
            font=style.FONT_MONO, corner_radius=8,
            border_color=style.BORDER, border_width=1)

        self.show_info = ctk.BooleanVar(value=True)
        self.show_debug = ctk.BooleanVar()
        self.debug_check = style.checkbox(
            log_frame, text="Debug Output",
            variable=self.show_debug, command=self.debug_tag)

        export_button = style.secondary_button(
            log_frame, text="Export Log...", command=self.export_log,
            width=130)

        header.grid(column=0, row=0, sticky="ew", padx=28, pady=(26, 18))
        log_frame.grid(column=0, row=1, sticky="nsew", padx=28, pady=(0, 28))

        status_label.grid(column=1, row=0, sticky="e", padx=16, pady=(14, 6))
        self.text.grid(column=0, row=1, columnspan=2,
                       sticky="NSEW", padx=16, pady=(0, 12))

        self.debug_check.grid(column=0, row=2, sticky="w", padx=16, pady=(0, 16))
        export_button.grid(row=2, column=1, sticky="e", padx=16, pady=(0, 16))

        log_frame.columnconfigure(0, weight=1)
        log_frame.columnconfigure(1, weight=1)
        log_frame.rowconfigure(1, weight=1)
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        # Output theme
        self.font = ("Courier", 10)
        # self.debug_tag() # Textbox tags work differently in CTk, for now we just use it as plain text or handle tags if supported
        # Note: ctk.CTkTextbox doesn't support tags as easily as tk.Text.
        # For simplicity in this modernization, we will focus on the look of the frame.

    def debug_tag(self):
        """Configures debug text tags, shown/hidden"""
        # CTkTextbox doesn't support tags/eliding as easily as tk.Text
        pass

    def start_watching(self, process, log_queue):
        """Starts watching a queue for log records until process ends"""
        self.process = process
        self.queue = log_queue
        self.finished = False
        self.dead_polls = 0
        self.status.set("Running")

        self.text.configure(state="normal")
        self.text.delete("1.0", "end")
        self.text.insert("end", "Starting task...\n")
        self.text.configure(state="disabled")

        self.after(1, self.update_loop)

    def handle_record(self, record: logging.LogRecord):
        """
        Display and formats a log record. The internal Text widget
        must be set to the active state before calling this function
        """
        levelname = record.levelname
        self.text.insert("end", f"[{levelname}] {record.getMessage()}\n")
        if record.exc_info:
            formatter = logging.Formatter()
            self.text.insert("end", formatter.formatException(record.exc_info))
            self.text.insert("end", "\n")

    def unexpected_end_message(self):
        """Build a more actionable message for an aborted worker/log stream."""
        exitcode = getattr(self.process, "exitcode", None)
        if exitcode is None:
            return "[ERROR] Task ended before the log stream finished.\n"

        return (
            "[ERROR] Task ended before the log stream finished. "
            f"Worker exit code: {exitcode}.\n"
        )

    def update_loop(self):
        """Updates the textbox with log messages"""

        self.text.configure(state="normal")

        while True:
            try:
                record = self.queue.get_nowait()
            except queue.Empty:
                break

            if record is None:
                self.finished = True
            else:
                self.handle_record(record)

        self.text.see("end")
        self.text.configure(state="disabled")

        if self.finished:
            self.status.set("Complete")
            return

        if self.process.is_alive():
            self.dead_polls = 0
            self.after(50, self.update_loop)
            return

        self.dead_polls += 1
        if self.dead_polls < 40:
            self.after(50, self.update_loop)
            return

        self.text.configure(state="normal")
        self.text.insert("end", self.unexpected_end_message())
        self.text.see("end")
        self.text.configure(state="disabled")
        self.finished = True
        exitcode = getattr(self.process, "exitcode", None)
        if exitcode is None:
            self.status.set("Log stream ended unexpectedly")
        else:
            self.status.set(f"Worker exited unexpectedly ({exitcode})")

    def export_log(self):
        """Save the current log to a file"""
        path = tk.filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text File", "*.txt"),
                       ("Log File", "*.log"),
                       ("All Files", "*.*")])

        if not path:
            return

        with open(path, 'w') as file:
            file.write('\n'.join(
                self.text.get('1.0', 'end').splitlines()
            ))

    def switch_to(self):
        """
        Disable the debug check if the log level is not debug
        """
        if int(self.app.getvar("LOG_LEVEL")) > logging.DEBUG:
            self.show_debug.set(False)
            self.debug_check.configure(state="disabled")
        else:
            self.debug_check.configure(state="normal")
