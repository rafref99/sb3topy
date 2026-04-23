"""
example.py

Contains the Examples tab of the GUI

TODO Avoid auto download when starting GUI?
Causes issues without internet
"""

import json
import logging
import tkinter as tk
import customtkinter as ctk
import webbrowser
from os import path

try:
    import requests
except ImportError:
    requests = None

from .. import config
from .. import packer
from ..parser import sanitizer
from . import style

logger = logging.getLogger(__name__)


class Example:
    """
    Represents an example project
    """

    def __init__(self, example):
        self.name = example['name']
        self.id = str(example['id'])
        self.download_link = "https://scratch.mit.edu/projects/" + \
            self.id + "/"

        self.thumb_link = "https://cdn2.scratch.mit.edu/get_image/project/" + \
            self.id + "_480x360.png"
        self.thumb_image = None

        self.viewer = example['description'].partition('\n')[0]
        self.view_link = example['link']

        self.username = '@' + example['author']
        self.user_link = "https://scratch.mit.edu/users/" + \
            example['author'] + "/"

        self.description = example['description'].partition('\n')[2]
        self.sha256 = example['sha256']
        self.config = example['config']

    def get_image(self):
        """Gets a PhotoImage of the example thumbnail"""
        if requests is None:
            logger.warning(
                "Failed to load thumbnail; requests not installed.")
            return None

        if self.thumb_image is None:
            try:
                from PIL import Image, ImageTk
                import io
                resp = requests.get(self.thumb_link)
                img_data = io.BytesIO(resp.content)
                img = Image.open(img_data)
                # Resize if necessary, but 480x360 should be fine
                self.thumb_image = ImageTk.PhotoImage(img)
            except ImportError:
                resp = requests.get(self.thumb_link)
                self.thumb_image = tk.PhotoImage(data=resp.content)
        return self.thumb_image


def read_examples():
    """Reads and returns the examples.json data"""
    # Get the path to the examples file
    if config.EXAMPLES_PATH is None:
        examples_path = path.join(path.dirname(__file__), "examples.json")
    else:
        examples_path = config.EXAMPLES_PATH

    # Attempt to read the json file
    try:
        with open(examples_path, 'r') as examples_file:
            return json.load(examples_file)
    except OSError:
        logger.exception(
            "Failed to load examples json '%s'", examples_path)
        return []
    except json.JSONDecodeError:
        logger.exception("Failed to parse examples json '%s'", examples_path)
        return []


class ExamplesFrame(ctk.CTkFrame):
    """
    Handles the Examples tab
    """

    def __init__(self, app, **kwargs):
        super().__init__(app, **kwargs, fg_color=style.APP_BG)
        self.app = app

        header = style.page_header(
            self, "Examples",
            "Download curated Scratch projects into your local examples folder.")

        # Create components
        content = ctk.CTkFrame(self, fg_color="transparent")
        list_frame = style.section(content, "Projects")
        self.examples_list = ctk.StringVar()
        # CustomTkinter does not have a Listbox, using tk.Listbox for now but styled
        self.listbox = tk.Listbox(
            list_frame, height=20, listvariable=self.examples_list,
            bg="#111827", fg="#f8fafc", selectbackground="#2563eb",
            selectforeground="#ffffff", activestyle="none",
            borderwidth=0, highlightthickness=0, font=("TkDefaultFont", 12))

        project_frame = style.section(content)

        self.thumbnail = ctk.CTkLabel(
            project_frame, text="Select a project", text_color=style.MUTED,
            fg_color=style.SURFACE_ALT, corner_radius=8)

        self.download_link_raw = ""
        self.download_link = ctk.StringVar(self.app, name="PROJECT_URL")

        download_frame = ctk.CTkFrame(project_frame, fg_color="transparent")
        download_box = style.entry(
            download_frame, textvariable=self.download_link)
        self.download_button = style.primary_button(
            download_frame, text="Download",
            command=self.download_project, width=100)
        self.download_run_button = style.success_button(
            download_frame, text="Download & Run",
            command=self.download_run_project, width=120)
        self.run_button = style.success_button(
            download_frame, text="Run",
            command=self.run_downloaded_project, width=100)
        self.redownload_button = style.secondary_button(
            download_frame, text="Redownload",
            command=self.download_project, width=110)

        self.project_viewer = ctk.StringVar()
        self.project_link = ctk.StringVar()
        self.username = ctk.StringVar()
        self.userlink = ctk.StringVar()
        self.project_desc = ctk.StringVar()
        self.json_sha = ctk.Variable(self.app, name="JSON_SHA")

        info_frame = ctk.CTkFrame(project_frame, fg_color="transparent")
        user_label = ctk.CTkLabel(
            info_frame, text="Made by", text_color=style.MUTED)
        user_link = Hyperlink(
            info_frame, self.userlink, textvariable=self.username)
        project_link = Hyperlink(
            info_frame, self.project_link, textvariable=self.project_viewer)
        description = ctk.CTkLabel(
            info_frame, textvariable=self.project_desc, wraplength=520,
            justify="left", text_color=style.TEXT)
        copyright_label = Hyperlink(
            info_frame, ctk.StringVar(
                value="https://creativecommons.org/licenses/by-sa/2.0/"),
            text="CC BY-SA-2.0")

        header.grid(column=0, row=0, sticky="ew", padx=28, pady=(26, 18))
        content.grid(column=0, row=1, sticky="nsew", padx=28, pady=(0, 28))

        list_frame.grid(column=0, row=0, sticky='NSEW', padx=(0, 14))
        self.listbox.grid(column=0, row=1, sticky='NSEW', pady=(0, 16), padx=16)

        project_frame.grid(column=1, row=0, sticky='NSEW')

        self.thumbnail.grid(column=0, row=0, sticky='NSEW', padx=16, pady=16)

        download_frame.grid(column=0, row=1, sticky='NEW', padx=16)
        download_box.grid(column=0, row=0, sticky='WE', padx=2)
        self.download_button.grid(column=1, row=0, sticky='NWE', padx=2)
        self.download_run_button.grid(
            column=2, row=0, sticky='NWE', padx=2)
        download_frame.columnconfigure(0, weight=1)

        info_frame.grid(column=0, row=2, sticky='NEW', padx=16, pady=16)
        user_label.grid(column=0, row=1, sticky='NW')
        user_link.grid(column=1, row=1, sticky='NW', padx=5)
        copyright_label.grid(column=2, row=1, sticky='NE')
        info_frame.columnconfigure(1, weight=1)

        project_link.grid(column=0, row=2, columnspan=3, sticky='NW', pady=(5, 0))

        description.grid(column=0, row=3, columnspan=3, sticky='NW', pady=5)

        # project_frame.columnconfigure(0, minsize=480*app.scale)
        # project_frame.rowconfigure(0, minsize=360*app.scale)

        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(1, weight=1)
        project_frame.columnconfigure(0, weight=1)
        project_frame.rowconfigure(0, weight=1)
        content.columnconfigure(0, minsize=260)
        content.columnconfigure(1, weight=1)
        content.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        # Bind events
        self.listbox.bind("<<ListboxSelect>>", self.listbox_changed)
        self.download_link.trace_add('write', self.download_changed)

        # Load examples data
        self.examples = [Example(example) for example in read_examples()]
        self.examples_list.set([example.name for example in self.examples])
        self.example = self.examples[0] if self.examples else None
        if self.examples:
            self.listbox.select_set(0)

    def download_changed(self, *_):
        """Called when the download link is changed"""
        if self.download_link.get() != self.example.download_link:
            self.thumbnail['image'] = ""
            self.json_sha.set(False)  # TODO New bool config for json_sha
        self.update_action_buttons()

    def listbox_changed(self, _):
        """Called when the listbox selection is changed by the user"""
        # Avoid weird events when on another tab
        selected = self.listbox.curselection()
        if selected and self.app.mode.get() == 'examples':
            self.example = self.examples[selected[0]]
            self.download_link.set("")
            self.update_project()

    def update_project(self):
        """Updates the project info"""
        dw_link = self.download_link.get()
        example = self.example

        # Don't update the project if the dw link is modified
        if dw_link and dw_link != example.download_link:
            self.thumbnail.configure(image=None, text="")
            self.listbox.selection_clear(0, "end")
            return

        image = example.get_image()
        if image:
            self.thumbnail.configure(image=image, text="")
        else:
            self.thumbnail.configure(image=None, text="Thumbnail failed to load")

        self.username.set(example.username)
        self.userlink.set(example.user_link)
        self.project_desc.set(example.description)

        self.project_viewer.set(example.viewer)
        self.project_link.set(example.view_link)

        self.download_link.set(example.download_link)

        self.json_sha.set(example.sha256)
        self.update_action_buttons()

    def example_output_path(self):
        """Return the persistent output folder for the selected example."""
        if self.example is None:
            return ""

        folder_name = sanitizer.clean_identifier(
            self.example.name, f"project_{self.example.id}")
        return path.join(
            path.expanduser("~"), "sb3topy_examples",
            f"{folder_name}_{self.example.id}")

    def example_is_downloaded(self):
        """Return whether the selected example has a runnable conversion."""
        output_path = self.example_output_path()
        return (
            path.isfile(path.join(output_path, "project.py")) and
            path.isdir(path.join(output_path, "engine")) and
            path.isfile(path.join(output_path, "engine", "runtime.py"))
        )

    def update_action_buttons(self):
        """Switch between download and run actions for examples."""
        if self.example is None:
            return

        for button in (
                self.download_button,
                self.download_run_button,
                self.run_button,
                self.redownload_button):
            button.grid_remove()

        if (
                self.download_link.get() == self.example.download_link and
                self.example_is_downloaded()):
            self.run_button.grid(column=1, row=0, sticky='NWE', padx=2)
            self.redownload_button.grid(column=2, row=0, sticky='NWE', padx=2)
        else:
            self.download_button.grid(column=1, row=0, sticky='NWE', padx=2)
            self.download_run_button.grid(
                column=2, row=0, sticky='NWE', padx=2)

    def _prepare_project_run(self, autorun):
        """Prepare the config for downloading an example project."""
        if self.example is None:
            return False

        if not self.download_link.get():
            self.update_project()

        self.app.setvar("AUTORUN", autorun)
        self.app.setvar("PROJECT_PATH", "")
        self.app.setvar("PROJECT_URL", self.download_link.get())
        self.app.setvar("PARSE_PROJECT", True)
        self.app.setvar("COPY_ENGINE", True)
        self.app.setvar("RECONVERT_IMAGES", True)

        self.app.setvar("OUTPUT_PATH", self.example_output_path())

        return True

    def run_downloaded_project(self):
        """Run an example that has already been downloaded and converted."""
        output_path = self.example_output_path()
        if not self.example_is_downloaded():
            self.update_action_buttons()
            return

        packer.launch_project(output_path)

    def download_project(self):
        """Downloads and converts the project"""
        if not self._prepare_project_run(False):
            return

        self.app.write_config()
        self.app.run_main()

    def download_run_project(self):
        """Downloads, converts, and runs the project"""
        if not self._prepare_project_run(True):
            return

        self.app.write_config()
        self.app.run_main()

    def switch_to(self):
        """Called when this tab is shown"""
        self.update_project()
        if self.download_link.get() != self.example.download_link:
            self.listbox.selection_clear(0, "end")


class Hyperlink(ctk.CTkLabel):
    """A label which goes to a webpage when clicked"""

    def __init__(self, parent, url, **kwargs):
        super().__init__(parent, text_color=style.ACCENT, cursor="hand2", **kwargs)
        self.url = url

        self.bind("<Enter>", self.mouse_enter)
        self.bind("<Leave>", self.mouse_leave)
        self.bind("<Button-1>", self.mouse_click)

    def mouse_enter(self, _):
        """Called when the mouse hovers"""
        self.configure(font=("TkDefaultFont", 9, "underline"))

    def mouse_leave(self, _):
        """Called when the mouse stops hovering"""
        self.configure(font=("TkDefaultFont", 9))

    def mouse_click(self, _):
        """Called when the mouse clicks"""
        webbrowser.open(self.url.get())
