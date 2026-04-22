"""
convert.py

Contains the Convert tab of the gui
"""

import tkinter as tk
from tkinter import filedialog
import customtkinter as ctk


class ConvertFrame(ctk.CTkFrame):
    """
    ConvertFrame
    """

    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self.app = parent

        self.project_path = ctk.StringVar(self.app, name="PROJECT_PATH")
        project_label = ctk.CTkLabel(self, text="Input Project:")
        project_box = ctk.CTkEntry(self, textvariable=self.project_path)
        project_button = ctk.CTkButton(
            self, text="Browse...", command=self.browse_project, width=100)

        self.output_path = ctk.StringVar(self.app, name="OUTPUT_PATH")
        folder_label = ctk.CTkLabel(self, text="Output Folder:")
        folder_box = ctk.CTkEntry(self, textvariable=self.output_path)
        folder_button = ctk.CTkButton(
            self, text="Browse...", command=self.browse_folder, width=100)

        convert_button = ctk.CTkButton(
            self, text="Convert Now", command=self.convert)

        # Grid everything
        project_label.grid(column=0, row=0, sticky="W", padx=20, pady=(20, 0))
        project_box.grid(column=0, row=1, columnspan=2, sticky="WE", padx=(20, 5), pady=5)
        project_button.grid(column=2, row=1, sticky="WE", padx=(0, 20), pady=5)

        folder_label.grid(column=0, row=2, sticky="W", padx=20, pady=(10, 0))
        folder_box.grid(column=0, row=3, columnspan=2, sticky="WE", padx=(20, 5), pady=5)
        folder_button.grid(column=2, row=3, sticky="WE", padx=(0, 20), pady=5)

        convert_button.grid(column=2, row=4, columnspan=1,
                            sticky="WE", pady=20, padx=(0, 20))

        self.columnconfigure(1, weight=1)

    def browse_project(self):
        """Show a dialog to select the project file"""
        path = filedialog.askopenfilename(
            filetypes=[("Project Files", "*.sb3"),
                       ("Zip Files", "*.zip"),
                       ("All Files", "*.*")])
        if path:
            self.app.setvar("PROJECT_PATH", path)

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
