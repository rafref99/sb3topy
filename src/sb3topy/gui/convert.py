"""
convert.py

Contains the Convert tab of the gui
"""

import tkinter as tk
from os import path as ospath
from tkinter import filedialog
import customtkinter as ctk

from . import style

try:
    from tkinterdnd2 import DND_FILES
except ImportError:
    DND_FILES = None


class ConvertFrame(ctk.CTkFrame):
    """
    ConvertFrame
    """

    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs, fg_color=style.APP_BG)
        self.app = parent

        header = style.page_header(
            self, "Convert Project",
            "Choose a Scratch project file and generate a runnable Python project.")

        content = ctk.CTkFrame(self, fg_color="transparent")

        self.project_path = ctk.StringVar(self.app, name="PROJECT_PATH")
        source_frame = style.section(content, "Source")
        project_label = ctk.CTkLabel(
            source_frame, text="Input project", text_color=style.MUTED,
            anchor="w")
        project_box = style.entry(
            source_frame, textvariable=self.project_path,
            placeholder_text="Select a .sb3 or .zip project")
        project_button = style.secondary_button(
            source_frame, text="Browse...", command=self.browse_project,
            width=110)
        self.enable_project_drop(source_frame, project_box)

        self.output_path = ctk.StringVar(self.app, name="OUTPUT_PATH")
        output_frame = style.section(content, "Destination")
        folder_label = ctk.CTkLabel(
            output_frame, text="Output folder", text_color=style.MUTED,
            anchor="w")
        folder_box = style.entry(
            output_frame, textvariable=self.output_path,
            placeholder_text="Choose where generated files should be saved")
        folder_button = style.secondary_button(
            output_frame, text="Browse...", command=self.browse_folder,
            width=110)

        action_frame = ctk.CTkFrame(content, fg_color="transparent")
        convert_button = style.success_button(
            action_frame, text="Convert and Run", command=self.convert,
            width=170)

        header.grid(column=0, row=0, sticky="ew", padx=28, pady=(26, 18))
        content.grid(column=0, row=1, sticky="nsew", padx=28, pady=(0, 28))

        source_frame.grid(column=0, row=0, sticky="ew", pady=(0, 14))
        project_label.grid(column=0, row=1, sticky="w", padx=16, pady=(2, 4))
        project_box.grid(column=0, row=2, sticky="ew", padx=(16, 8), pady=(0, 16))
        project_button.grid(column=1, row=2, sticky="ew", padx=(0, 16), pady=(0, 16))

        output_frame.grid(column=0, row=1, sticky="ew", pady=(0, 18))
        folder_label.grid(column=0, row=1, sticky="w", padx=16, pady=(2, 4))
        folder_box.grid(column=0, row=2, sticky="ew", padx=(16, 8), pady=(0, 16))
        folder_button.grid(column=1, row=2, sticky="ew", padx=(0, 16), pady=(0, 16))

        action_frame.grid(column=0, row=2, sticky="e")
        convert_button.grid(column=0, row=0, sticky="e")

        source_frame.columnconfigure(0, weight=1)
        output_frame.columnconfigure(0, weight=1)
        content.columnconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

    def browse_project(self):
        """Show a dialog to select the project file"""
        project_path = filedialog.askopenfilename(
            filetypes=[("Project Files", "*.sb3"),
                       ("Zip Files", "*.zip"),
                       ("All Files", "*.*")])
        if project_path:
            self.set_project_path(project_path)

    def enable_project_drop(self, *widgets):
        """Register file-drop handlers when tkinterdnd2 is available."""
        if DND_FILES is None:
            return

        for widget in widgets:
            register = getattr(widget, "drop_target_register", None)
            bind = getattr(widget, "dnd_bind", None)
            if register is None or bind is None:
                continue

            register(DND_FILES)
            bind("<<Drop>>", self.drop_project)

    def drop_project(self, event):
        """Handle one or more files dropped onto the project input."""
        project_path = self.choose_project_path(
            self.drop_paths(event.data, self.app.tk.splitlist))
        if project_path:
            self.set_project_path(project_path)
        return "break"

    def set_project_path(self, project_path):
        """Set the selected local project and clear remote-project state."""
        self.app.setvar("PROJECT_PATH", project_path)
        self.app.setvar("PROJECT_URL", "")
        self.app.setvar("JSON_SHA", False)

    @staticmethod
    def drop_paths(data, splitlist):
        """Parse Tk drop data into paths."""
        if not data:
            return []

        try:
            return [item for item in splitlist(data) if item]
        except tk.TclError:
            return [data]

    @staticmethod
    def choose_project_path(paths):
        """Return the first dropped Scratch project path."""
        for project_path in paths:
            if ospath.splitext(project_path)[1].lower() in {".sb3", ".zip"}:
                return project_path
        return ""

    def browse_folder(self):
        """Show a dialog to select the output folder"""
        output_path = filedialog.askdirectory()
        if output_path:
            self.output_path.set(output_path)

    def convert(self):
        """Run the converter"""
        self.app.setvar("AUTORUN", True)
        self.app.setvar("PROJECT_URL", "")
        self.app.setvar("JSON_SHA", False)
        self.app.setvar("PARSE_PROJECT", True)
        self.app.setvar("COPY_ENGINE", True)
        self.app.write_config()
        self.app.run_main()

    # def browse_zip(self):
    #     """Show a dialog to select the output zip path"""
    #     path = filedialog.asksaveasfilename(
    #         defaultextension=".zip",
    #         filetypes=[("ZIP Files", "*.zip"),
    #                    ("All Files", "*.*")])
    #     if path:
    #         self.zip_path.set(path)

    # def browse_exe(self):
    #     """Show a dialog to select the output exe path"""
    #     path = filedialog.asksaveasfilename(
    #         defaultextension=".exe",
    #         filetypes=[("EXE Files", "*.exe"),
    #                    ("All Files", "*.*")])
    #     if path:
    #         self.exe_path.set(path)
