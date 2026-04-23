"""
settings.py

Contains the Settings tab of the gui

Locks config path to config path in src/sb3topy/config/config.json


General:
    File Paths
        Project path
        Project url
        Output path

        zip path
        exe path

    Quick Config:
        fps
        turbo mode
        clone limit
        list limit
        master volume
        svg scale
        type guessing
        debug json

Assets:
    Integrity
        verify
        reconvert images
        reconvert sounds

    Workers
        download workers
        conversion workers
        timeout

    SVGs
        svg command
        svg scale

    MP3s
        mp3 command
        enable conversion

Optimizations:
    Basic
        legacy lists
        var types
        arg types
        static lists
        solo broadcasts

    Advanced
        disable any cast
        aggressive num cast
        changed num cast
        disable str cast
        disable int cast
        warp all

Project:
    Timings
        target fps
        turbo
        work time
        warp time

    Display
        stage size
        display size
        allow resize
        scaled display
        fs scale

    Title
        text
        enable

    Audio
        channels
        master volume

    Limits
        clones
        max list

    Hotkeys
        turbo hotkey
        fullscreen hotkey
        debug hotkeys

    Miscellaneous
        username
        draw fps
        random seed

Debug
    Debug
        debug json
        format json
        overwrite engine

Export:
    Ask for file
    If is autoload, prompt to turn on
    Save
    Update buttons

Save:
    If exists and is not last loaded, prompt
    Update last loaded
    Update buttons

Load:
    Load
    Set last loaded

"""

import tkinter as tk
from os import path
from tkinter import filedialog, messagebox
import customtkinter as ctk

from .. import config
from . import style


class SettingsFrame(ctk.CTkFrame):
    """Handles the Settings tab"""

    def __init__(self, app, **kwargs):
        super().__init__(app, **kwargs, fg_color=style.APP_BG)
        self.app = app

        self.tabview = ctk.CTkTabview(
            self, fg_color=style.SURFACE, segmented_button_fg_color=style.SURFACE_ALT,
            segmented_button_selected_color=style.ACCENT,
            segmented_button_selected_hover_color=style.ACCENT_ACTIVE_HOVER,
            segmented_button_unselected_color=style.BORDER,
            segmented_button_unselected_hover_color=style.SURFACE_ALT,
            text_color=style.TEXT,
            text_color_disabled=style.MUTED,
            corner_radius=8)
        self.tabview.pack(fill="both", expand=True, padx=28, pady=28)

        self.general_tab = self.tabview.add("General")
        self.project_tab = self.tabview.add("Project")
        self.assets_tab = self.tabview.add("Assets")
        self.opts_tab = self.tabview.add("Optimizations")
        self.debug_tab = self.tabview.add("Debug")

        self.general = GeneralSettings(app, self.general_tab)
        self.assets = AssetSettings(app, self.assets_tab)
        self.opts = OptimizationSettings(app, self.opts_tab)
        self.project = ProjectFrame(app, self.project_tab)
        self.debug = DebugFrame(app, self.debug_tab)

        self.general.pack(fill="both", expand=True)
        self.assets.pack(fill="both", expand=True)
        self.opts.pack(fill="both", expand=True)
        self.project.pack(fill="both", expand=True)
        self.debug.pack(fill="both", expand=True)

        self.tabview.configure(command=self.switch)

    def switch(self, *_):
        """Called when the tab is switched"""
        self.general.switch()
        self.project.switch()
        self.assets.cairo_toggle()
        self.debug.switch()


class GeneralSettings(ctk.CTkFrame):
    """Handles the General tab of settings"""

    def __init__(self, app, parent, **kwargs):
        super().__init__(parent, **kwargs, fg_color="transparent")
        self.app = app

        paths_frame = style.section(self)
        quick_frame = style.section(self)
        config_frame = style.section(self)

        self.project_path = ctk.StringVar(app, name="PROJECT_PATH")
        self.project_url = ctk.StringVar(app, name="PROJECT_URL")
        self.output_path = ctk.StringVar(app, name="OUTPUT_PATH")

        ctk.CTkLabel(paths_frame, text="Paths", font=("", 12, "bold")).grid(row=0, column=0, sticky="w", padx=10, pady=5)
        path_label = ctk.CTkLabel(paths_frame, text="Project Path:")
        path_box = ctk.CTkEntry(paths_frame, textvariable=self.project_path)
        url_label = ctk.CTkLabel(paths_frame, text="Project URL:")
        url_box = ctk.CTkEntry(paths_frame, textvariable=self.project_url)
        output_label = ctk.CTkLabel(paths_frame, text="Output Path:")
        output_box = ctk.CTkEntry(paths_frame, textvariable=self.output_path)

        self.target_fps = ctk.IntVar(app, name="TARGET_FPS")
        self.turbo_mode = ctk.BooleanVar(app, name="TURBO_MODE")
        self.clone_limit = ctk.BooleanVar()
        self.list_limit = ctk.BooleanVar()
        self.master_volume = ctk.IntVar(app, name="MASTER_VOLUME")
        self.svg_scale = ctk.IntVar(app, name="SVG_SCALE")
        self.type_guessing = ctk.IntVar()
        self.debug_json = ctk.BooleanVar(app, name="DEBUG_JSON")

        ctk.CTkLabel(quick_frame, text="Quick Config", font=("", 12, "bold")).grid(row=0, column=0, sticky="w", padx=10, pady=5)
        fps_label = ctk.CTkLabel(quick_frame, text="Target FPS:")
        fps_spin = ctk.CTkEntry(
            quick_frame, width=70,
            textvariable=self.target_fps)
        turbo_check = ctk.CTkCheckBox(
            quick_frame, text="Turbo Mode", variable=self.turbo_mode)
        clone_check = ctk.CTkCheckBox(
            quick_frame, text="Clone Limit", variable=self.clone_limit,
            command=self.clone_toggle)
        list_check = ctk.CTkCheckBox(
            quick_frame, text="List Limit", variable=self.list_limit,
            command=self.list_toggle)
        volume_label = ctk.CTkLabel(quick_frame, text="Master Volume:")
        volume_spin = ctk.CTkEntry(
            quick_frame, width=70,
            textvariable=self.master_volume)
        type_check = ctk.CTkCheckBox(
            quick_frame, text="Type Guessing", variable=self.type_guessing,
            command=self.type_guess_toggle)
        json_check = ctk.CTkCheckBox(
            quick_frame, text="Save project.json", variable=self.debug_json)

        self.config_path = ctk.StringVar(app, name="CONFIG_PATH")
        self.autoload = ctk.BooleanVar(app, name="AUTOLOAD_CONFIG")
        self.autoload.set(True)

        # If autoload is None, config_path is not None
        self.autoload_saved = config.AUTOLOAD_CONFIG
        if config.AUTOLOAD_CONFIG is None:
            self.last_saved = config.CONFIG_PATH
        elif config.AUTOLOAD_CONFIG:
            self.last_saved = config.AUTOLOAD_PATH
        else:
            self.last_saved = ""

        ctk.CTkLabel(config_frame, text="Configuration File", font=("", 12, "bold")).grid(row=0, column=0, sticky="w", padx=10, pady=5)
        config_label = ctk.CTkLabel(config_frame, text="Path:")
        config_box = ctk.CTkEntry(config_frame, textvariable=self.config_path)
        action_frame = ctk.CTkFrame(config_frame, fg_color="transparent")
        export_button = ctk.CTkButton(
            config_frame, text="Export...", command=self.config_export, width=100)
        self.save_button = ctk.CTkButton(
            action_frame, text="Save", command=self.config_save, width=100)
        self.load_button = ctk.CTkButton(
            action_frame, text="Load", command=self.config_load, width=100)
        self.load_check = ctk.CTkCheckBox(
            config_frame, text="Load on Start",
            variable=self.autoload, command=self.update_buttons)
        # TODO Restore defaults button

        self.config_path.trace_add("write", self.update_buttons)
        self.update_buttons()

        path_label.grid(column=0, row=1, sticky='W', padx=10, pady=5)
        path_box.grid(column=1, row=1, sticky='EW',
                      padx=3, pady=3, columnspan=2)
        url_label.grid(column=0, row=2, sticky='W', padx=10, pady=5)
        url_box.grid(column=1, row=2, sticky='EW',
                     padx=3, pady=3, columnspan=2)
        output_label.grid(column=0, row=3, sticky='W', padx=10, pady=5)
        output_box.grid(column=1, row=3, sticky='EW',
                        padx=3, pady=3, columnspan=2)

        fps_label.grid(column=0, row=1, sticky='W', padx=10, pady=5)
        fps_spin.grid(column=1, row=1, sticky='W', padx=3, pady=3)
        volume_label.grid(column=0, row=2, sticky='W', padx=10, pady=5)
        volume_spin.grid(column=1, row=2, sticky='W', padx=3, pady=3)
        turbo_check.grid(column=2, row=1, columnspan=2, sticky='W', padx=10)
        clone_check.grid(column=0, row=3, columnspan=1, sticky='W', padx=10)
        list_check.grid(column=1, row=3, columnspan=2, sticky='W', padx=10)
        type_check.grid(column=0, row=4, columnspan=2, sticky='W', padx=10)
        json_check.grid(column=0, row=5, columnspan=2, sticky='W', padx=10, pady=(0, 10))

        config_label.grid(column=0, row=1, sticky="W", padx=10)
        self.load_check.grid(column=1, row=1, sticky="W", padx=6, columnspan=3)
        config_box.grid(column=0, row=2, sticky="EW",
                        padx=10, pady=5, columnspan=3)
        export_button.grid(column=3, row=2, sticky="EW", padx=(2, 10), pady=5)
        action_frame.grid(column=0, row=3, sticky="E", padx=10, pady=(0, 12),
                          columnspan=4)
        self.save_button.grid(column=0, row=0, sticky="EW", padx=(0, 6))
        self.load_button.grid(column=1, row=0, sticky="EW")

        paths_frame.grid(column=0, row=0, sticky="NSEW", padx=10, pady=5)
        quick_frame.grid(column=0, row=1, sticky="NSEW", padx=10, pady=5)
        config_frame.grid(column=0, row=2, sticky="SEW", padx=10, pady=5)

        paths_frame.columnconfigure(1, weight=1)
        quick_frame.columnconfigure(2, weight=1)
        config_frame.columnconfigure(1, weight=1)
        config_frame.columnconfigure(2, weight=1)

        self.columnconfigure(0, weight=1)
        self.rowconfigure(2, weight=1)

    def type_guess_toggle(self, _=None):
        """Called when the type_gussing checkbox is toggled"""
        value = self.type_guessing.get()
        if value == 0:
            self.app.setvar("VAR_TYPES", False)
            self.app.setvar("ARG_TYPES", False)
        elif value == 1:
            self.app.setvar("VAR_TYPES", True)
            self.app.setvar("ARG_TYPES", True)
        # value is 2 during mixed state

    def clone_toggle(self):
        """Called when the clone limit checkbox is toggled"""
        if self.clone_limit.get():
            self.app.setvar("MAX_CLONES", config.project.MAX_CLONES)
        else:
            self.app.setvar("MAX_CLONES", 0)

    def list_toggle(self):
        """CAlled when the list limit checkbox is toggled"""
        if self.list_limit.get():
            self.app.setvar("MAX_LIST", config.project.MAX_LIST)
        else:
            self.app.setvar("MAX_LIST", 0)

    def switch(self):
        """Called when the tab is switched to"""
        var_types = self.app.getvar("VAR_TYPES")
        arg_types = self.app.getvar("ARG_TYPES")

        if var_types == arg_types:
            self.type_guessing.set(var_types)
        else:
            self.type_guessing.set(2)

        self.list_limit.set(self.app.getvar("MAX_LIST"))
        self.clone_limit.set(self.app.getvar("MAX_CLONES"))

    def config_changed(self):
        """Called when focus leaves the config path entry"""
        if not self.config_path.get():
            self.config_path.set(config.AUTOLOAD_PATH)

    def config_export(self):
        """Browse to export config"""
        # Prompt for a file
        config_path = filedialog.asksaveasfilename(
            filetypes=[("JSON Files", "*.json"),
                       ("All Files", "*.*")])

        if samefile_safe(config_path, config.AUTOLOAD_PATH):
            # Prompt to enable autoload
            if not self.autoload.get():
                self.autoload.set(messagebox.askyesno(
                    "sb3topy", (
                        "Would you like to load these settings next "
                        "time sb3topy opens?")
                ))

            # Update the saved autoload value
            self.autoload_saved = self.autoload.get()

        if config_path:
            # Update the config path
            self.config_path.set(config_path)

            # Save the config data
            self.app.write_config()
            config.save_config(config_path)

            # Update button states
            self.update_buttons()

    def config_save(self):
        """Save to the config path"""
        # Get the config path
        config_path = self.config_path.get()

        # Prompt for overwriting files
        if samefile_safe(config_path, self.last_saved) is False:
            basename = path.basename(config_path)
            result = messagebox.askyesno(
                "sb3topy",
                f"{basename} already exists.\nDo you want to replace it?",
                icon="warning")
            if not result:
                return

        # Update the saved autoload value
        if samefile_safe(config_path, config.AUTOLOAD_PATH):
            self.autoload_saved = self.autoload.get()

        # Update the last loaded value
        self.last_saved = config_path

        # Save the config data
        self.app.write_config()
        config.save_config(config_path)

        # Update button states
        self.update_buttons()

    def config_load(self):
        """Load from the config path"""
        config_path = self.config_path.get()

        # Load config
        config.load_config(config_path)
        self.app.read_config()

        # Update last saved
        self.last_saved = config_path
        self.update_buttons()

    def update_buttons(self, *_):
        """Called to update the state of the load button and check"""
        config_path = self.config_path.get()

        # Disable load if it isn't a file
        if path.isfile(config_path):
            self.load_button.configure(state="normal")
        else:
            self.load_button.configure(state="disabled")

        # Disable autoload if it isn't the autoload config
        if samefile_safe(config_path, config.AUTOLOAD_PATH):
            # Enable the check
            self.load_check.configure(state="normal")

            # Update the unsaved marker
            if self.autoload.get() == self.autoload_saved:
                self.load_check["text"] = "Load on Start"
            else:
                self.load_check["text"] = "Load on Start*"

        else:
            # Disable the check
            self.load_check.configure(state="disabled")

            # Change the check to the saved state
            self.load_check["text"] = "Load on Start"
            self.autoload.set(bool(self.autoload_saved))  # TODO Error here

        # Disable save if it isn't a valid directory
        if path.isdir(path.dirname(config_path)):
            self.save_button.configure(state="normal")
        else:
            self.save_button.configure(state="disabled")
        return True


def samefile_safe(path1, path2):
    """
    Checks if two files are the same, catching errors. If an error
    occurs, eg. because one file doesn't exist, None will be returned.

    May not work correctly with symlinks.
    """
    try:
        return path.samefile(path1, path2)
    except OSError:
        return None


class AssetSettings(ctk.CTkFrame):
    """Handles the Assets tab of settings"""

    def __init__(self, app, parent, **kwargs):
        super().__init__(parent, **kwargs, fg_color="transparent")
        self.app = app

        integ_frame = style.section(self)
        worker_frame = style.section(self)
        svg_frame = style.section(self)
        mp3_frame = style.section(self)

        self.verify_assets = ctk.BooleanVar(app, name="VERIFY_ASSETS")
        self.reconvert_images = ctk.BooleanVar(app, name="RECONVERT_IMAGES")
        self.reconvert_sounds = ctk.BooleanVar(app, name="RECONVERT_SOUNDS")

        ctk.CTkLabel(integ_frame, text="Integrity", font=("", 12, "bold")).grid(row=0, column=0, sticky="w", padx=10, pady=5)
        verify_check = ctk.CTkCheckBox(
            integ_frame, text="Verify Assets", variable=self.verify_assets)
        re_images_check = ctk.CTkCheckBox(
            integ_frame, text="Reconvert Images",
            variable=self.reconvert_images)
        re_sounds_check = ctk.CTkCheckBox(
            integ_frame, text="Reconvert Sounds",
            variable=self.reconvert_sounds)

        self.download_workers = ctk.IntVar(app, name="DOWNLOAD_THREADS")
        self.convert_workers = ctk.IntVar(app, name="CONVERT_THREADS")
        self.convert_timeout = ctk.IntVar(app, name="CONVERT_TIMEOUT")

        ctk.CTkLabel(worker_frame, text="Workers", font=("", 12, "bold")).grid(row=0, column=0, sticky="w", padx=10, pady=5)
        dw_workers_label = ctk.CTkLabel(worker_frame, text="Download Workers:")
        dw_workers_spin = ctk.CTkEntry(
            worker_frame, textvariable=self.download_workers, width=70)
        cv_workers_label = ctk.CTkLabel(worker_frame, text="Convert Workers:")
        self.cv_workers_spin = ctk.CTkEntry(
            worker_frame, textvariable=self.convert_workers, width=70)
        timeout_label = ctk.CTkLabel(worker_frame, text="Timeout (s):")
        timeout_spin = ctk.CTkEntry(
            worker_frame, textvariable=self.convert_timeout, width=70)

        self.use_svg_cmd = ctk.BooleanVar(app, name="USE_SVG_CMD")
        self.svg_command = ctk.StringVar(app, name="SVG_COMMAND")
        self.svg_scale = ctk.IntVar(app, name="SVG_SCALE")
        self.convert_costumes = ctk.BooleanVar(app, name="CONVERT_COSTUMES")

        ctk.CTkLabel(svg_frame, text="SVGs", font=("", 12, "bold")).grid(row=0, column=0, sticky="w", padx=10, pady=5)
        svg_cairo_box = ctk.CTkCheckBox(
            svg_frame, text="Use SVG Command",
            variable=self.use_svg_cmd, command=self.cairo_toggle)
        svg_comm_label = ctk.CTkLabel(svg_frame, text="Convert Command:")
        self.svg_comm_box = ctk.CTkEntry(svg_frame, textvariable=self.svg_command)
        svg_scale_label = ctk.CTkLabel(svg_frame, text="Converted Scale:")
        svg_scale_spin = ctk.CTkEntry(svg_frame, width=70,
                                     textvariable=self.svg_scale)
        convert_svg_check = ctk.CTkCheckBox(svg_frame, text="Convert costumes",
                                            variable=self.convert_costumes)

        self.mp3_command = ctk.StringVar(app, name="MP3_COMMAND")
        self.convert_sounds = ctk.BooleanVar(app, name="CONVERT_SOUNDS")

        ctk.CTkLabel(mp3_frame, text="MP3s", font=("", 12, "bold")).grid(row=0, column=0, sticky="w", padx=10, pady=5)
        mp3_comm_label = ctk.CTkLabel(mp3_frame, text="Convert Command:")
        mp3_comm_box = ctk.CTkEntry(mp3_frame, textvariable=self.mp3_command)
        convert_mp3_check = ctk.CTkCheckBox(mp3_frame, text="Convert sounds",
                                            variable=self.convert_sounds)

        verify_check.grid(column=0, row=0, sticky="W")
        re_images_check.grid(column=0, row=1, sticky="W", padx=10)
        re_sounds_check.grid(column=0, row=2, sticky="W", padx=10, pady=(0, 10))

        dw_workers_label.grid(column=0, row=1, sticky="W", padx=10)
        dw_workers_spin.grid(column=1, row=1, sticky="W", padx=3, pady=3)
        cv_workers_label.grid(column=0, row=2, sticky="W", padx=10)
        self.cv_workers_spin.grid(column=1, row=2, sticky="W", padx=3, pady=3)
        timeout_label.grid(column=0, row=3, sticky="W", padx=10)
        timeout_spin.grid(column=1, row=3, sticky="W", padx=3, pady=(3, 10))

        svg_cairo_box.grid(column=0, row=1, sticky="W", padx=10)
        svg_comm_label.grid(column=0, row=2, sticky="W", padx=10)
        self.svg_comm_box.grid(column=1, row=2, sticky="EW", padx=3, pady=3)
        svg_scale_label.grid(column=0, row=3, sticky="W", padx=10)
        svg_scale_spin.grid(column=1, row=3, sticky="W", padx=3, pady=3)
        convert_svg_check.grid(column=0, row=4, sticky="W", padx=10, pady=(0, 10))

        mp3_comm_label.grid(column=0, row=1, sticky="W", padx=10)
        mp3_comm_box.grid(column=1, row=1, sticky="EW", padx=3, pady=3)
        convert_mp3_check.grid(column=0, row=2, sticky="W", padx=10, pady=(0, 10))

        integ_frame.grid(column=0, row=0, sticky="NSEW", padx=10, pady=5)
        worker_frame.grid(column=0, row=1, sticky="NSEW", padx=10, pady=5)
        svg_frame.grid(column=1, row=0, sticky="NSEW", padx=10, pady=5)
        mp3_frame.grid(column=1, row=1, sticky="NSEW", padx=10, pady=5)

        integ_frame.columnconfigure(1, weight=1)
        worker_frame.columnconfigure(1, weight=1)
        svg_frame.columnconfigure(1, weight=1)
        mp3_frame.columnconfigure(1, weight=1)

        self.columnconfigure(0, weight=1)

    def cairo_toggle(self):
        """Called when USE_SVG_CMD is toggled"""
        if self.use_svg_cmd.get():
            self.svg_comm_box.configure(state="normal")
        else:
            self.svg_comm_box.configure(state="disabled")


class OptimizationSettings(ctk.CTkFrame):
    """Handles the Optimizations tab of settings"""

    def __init__(self, app, parent, **kwargs):
        super().__init__(parent, **kwargs, fg_color="transparent")
        self.app = app

        toggle_frame = style.section(self)
        compat_frame = style.section(self)
        adv_frame = style.section(self)

        self.static_lists = ctk.BooleanVar(app, name="LIST_TYPES")
        self.var_types = ctk.BooleanVar(app, name="VAR_TYPES")
        self.arg_types = ctk.BooleanVar(app, name="ARG_TYPES")
        self.solo_broadcasts = ctk.BooleanVar(app, name="SOLO_BROADCASTS")
        self.warp_all = ctk.BooleanVar(app, name="WARP_ALL")

        ctk.CTkLabel(toggle_frame, text="Toggles", font=("", 12, "bold")).grid(row=0, column=0, sticky="w", padx=10, pady=5)
        var_check = ctk.CTkCheckBox(
            toggle_frame, text="Variable Type Guessing", variable=self.var_types)
        arg_check = ctk.CTkCheckBox(
            toggle_frame, text="CB Arg Type Guessing", variable=self.arg_types)
        static_check = ctk.CTkCheckBox(
            toggle_frame, text="Static Lists", variable=self.static_lists)
        solo_check = ctk.CTkCheckBox(
            toggle_frame, text="Solo Broadcast Detection",
            variable=self.solo_broadcasts)
        warp_check = ctk.CTkCheckBox(
            toggle_frame, text="Warp All (Not Recommended)", variable=self.warp_all)

        self.legacy_lists = ctk.BooleanVar(app, name="LEGACY_LISTS")
        self.disable_int = ctk.BooleanVar(app, name="DISABLE_INT_CAST")

        ctk.CTkLabel(compat_frame, text="Compatibility", font=("", 12, "bold")).grid(row=0, column=0, sticky="w", padx=10, pady=5)
        legacy_check = ctk.CTkCheckBox(
            compat_frame, text="Legacy Lists", variable=self.legacy_lists)
        dint_check = ctk.CTkCheckBox(
            compat_frame, text="Disable Int Cast", variable=self.disable_int)

        self.disable_any = ctk.BooleanVar(app, name="DISABLE_ANY_CAST")
        self.aggressive_num = ctk.BooleanVar(app, name="AGGRESSIVE_NUM_CAST")
        self.changed_num = ctk.BooleanVar(app, name="CHANGED_NUM_CAST")
        self.disable_str = ctk.BooleanVar(app, name="DISABLE_STR_CAST")

        ctk.CTkLabel(adv_frame, text="Advanced Casting", font=("", 12, "bold")).grid(row=0, column=0, sticky="w", padx=10, pady=5)
        dany_check = ctk.CTkCheckBox(
            adv_frame, text="Disable Any Cast", variable=self.disable_any)
        dstr_check = ctk.CTkCheckBox(
            adv_frame, text="Relaxed Str Cast", variable=self.disable_str)
        changed_check = ctk.CTkCheckBox(
            adv_frame, text="Changed Var Cast", variable=self.changed_num)
        aggressive_check = ctk.CTkCheckBox(
            adv_frame, text="Aggressive Num Cast",
            variable=self.aggressive_num)

        var_check.grid(column=0, row=1, sticky="W", padx=10)
        arg_check.grid(column=0, row=2, sticky="W", padx=10)
        static_check.grid(column=0, row=3, sticky="W", padx=10)
        solo_check.grid(column=0, row=4, sticky="W", padx=10)
        warp_check.grid(column=0, row=5, sticky="W", padx=10, pady=(0, 10))

        legacy_check.grid(column=0, row=1, sticky="W", padx=10)
        dint_check.grid(column=0, row=2, sticky="W", padx=10, pady=(0, 10))

        dany_check.grid(column=0, row=1, sticky="W", padx=10)
        dstr_check.grid(column=0, row=2, sticky="W", padx=10)
        aggressive_check.grid(column=0, row=3, sticky="W", padx=10)
        changed_check.grid(column=0, row=4, sticky="W", padx=10, pady=(0, 10))

        toggle_frame.grid(column=0, row=0, sticky="NSEW", padx=10, pady=5)
        compat_frame.grid(column=0, row=1, sticky="NSEW", padx=10, pady=5)
        adv_frame.grid(column=0, row=2, sticky="NSEW", padx=10, pady=5)

        toggle_frame.columnconfigure(0, weight=1)
        compat_frame.columnconfigure(0, weight=1)
        adv_frame.columnconfigure(0, weight=1)

        self.columnconfigure(0, weight=1)


class ProjectFrame(ctk.CTkFrame):
    """Handles the Project tab of settings"""

    def __init__(self, app, parent, **kwargs):
        super().__init__(parent, **kwargs, fg_color="transparent")
        self.app = app

        timing_frame = style.section(self)
        display_frame = style.section(self)
        title_frame = style.section(self)
        audio_frame = style.section(self)
        limits_frame = style.section(self)
        hotkey_frame = style.section(self)
        misc_frame = style.section(self)

        self.target_fps = ctk.IntVar(app, name="TARGET_FPS")
        self.turbo_mode = ctk.BooleanVar(app, name="TURBO_MODE")
        self.iwork_time = ctk.IntVar(app, name="WORK_TIME_INV")
        self.warp_time = ctk.IntVar(app, name="WARP_TIME")

        ctk.CTkLabel(timing_frame, text="Timings", font=("", 12, "bold")).grid(row=0, column=0, sticky="w", padx=10, pady=5)
        fps_label = ctk.CTkLabel(timing_frame, text="Target FPS:")
        fps_spin = ctk.CTkEntry(timing_frame, width=70,
                               textvariable=self.target_fps)
        turbo_check = ctk.CTkCheckBox(
            timing_frame, text="Turbo Mode", variable=self.turbo_mode)
        warp_label = ctk.CTkLabel(timing_frame, text="Warp Time (s):")
        warp_spin = ctk.CTkEntry(timing_frame, width=70,
                                textvariable=self.warp_time)
        work_label = ctk.CTkLabel(timing_frame, text="Work Time (1/s):")
        work_spin = ctk.CTkEntry(timing_frame, width=70,
                                textvariable=self.iwork_time)

        self.stage_width = ctk.IntVar(app, name="STAGE_WIDTH")
        self.stage_height = ctk.IntVar(app, name="STAGE_HEIGHT")
        self.display_width = ctk.IntVar(app, name="DISPLAY_WIDTH")
        self.display_height = ctk.IntVar(app, name="DISPLAY_HEIGHT")
        self.allow_resize = ctk.BooleanVar(app, name="ALLOW_RESIZE")
        self.scaled_display = ctk.BooleanVar(app, name="SCALED_DISPLAY")
        self.fs_scale = ctk.IntVar(app, name="FS_SCALE")

        ctk.CTkLabel(display_frame, text="Display", font=("", 12, "bold")).grid(row=0, column=0, sticky="w", padx=10, pady=5)
        stage_label = ctk.CTkLabel(display_frame, text="Stage Size:")
        stagew_spin = ctk.CTkEntry(
            display_frame, width=70,
            textvariable=self.stage_width)
        stageh_spin = ctk.CTkEntry(
            display_frame, width=70,
            textvariable=self.stage_height)
        display_label = ctk.CTkLabel(display_frame, text="Display Size:")
        displayw_spin = ctk.CTkEntry(
            display_frame, width=70,
            textvariable=self.display_width)
        displayh_spin = ctk.CTkEntry(
            display_frame, width=70,
            textvariable=self.display_height)
        resize_check = ctk.CTkCheckBox(
            display_frame, text="Resizable Display",
            variable=self.allow_resize)
        scaled_check = ctk.CTkCheckBox(
            display_frame, text="Scaled Display",
            variable=self.scaled_display)
        fs_label = ctk.CTkLabel(display_frame, text="Fullscreen Scale:")
        fs_spin = ctk.CTkEntry(
            display_frame, width=70,
            textvariable=self.fs_scale)

        self.title_text = ctk.StringVar(app, name="TITLE")
        self.dynamic_title = ctk.BooleanVar(app, name="DYNAMIC_TITLE")

        ctk.CTkLabel(title_frame, text="Title", font=("", 12, "bold")).grid(row=0, column=0, sticky="w", padx=10, pady=5)
        title_label = ctk.CTkLabel(title_frame, text="Title Text:")
        title_box = ctk.CTkEntry(title_frame, textvariable=self.title_text)
        title_check = ctk.CTkCheckBox(
            title_frame, text="Dynamic Title",
            variable=self.dynamic_title)

        self.audio_channels = ctk.IntVar(app, name="AUDIO_CHANNELS")
        self.master_volume = ctk.IntVar(app, name="MASTER_VOLUME")

        ctk.CTkLabel(audio_frame, text="Audio", font=("", 12, "bold")).grid(row=0, column=0, sticky="w", padx=10, pady=5)
        channels_label = ctk.CTkLabel(audio_frame, text="Mixer Channels:")
        channels_spin = ctk.CTkEntry(
            audio_frame, width=70,
            textvariable=self.audio_channels)
        volume_label = ctk.CTkLabel(audio_frame, text="Master Volume:")
        volume_spin = ctk.CTkEntry(
            audio_frame, width=70,
            textvariable=self.master_volume)

        self.max_clones = ctk.IntVar(app, name="MAX_CLONES")
        self.clone_limit = ctk.BooleanVar(value=True)
        self.max_list = ctk.IntVar(app, name="MAX_LIST")
        self.list_limit = ctk.BooleanVar(value=True)

        ctk.CTkLabel(limits_frame, text="Limits", font=("", 12, "bold")).grid(row=0, column=0, sticky="w", padx=10, pady=5)
        clones_label = ctk.CTkLabel(limits_frame, text="Clone Limit:")
        self.clones_spin = ctk.CTkEntry(
            limits_frame, width=100,
            textvariable=self.max_clones)
        clones_check = ctk.CTkCheckBox(
            limits_frame, text="Enable?",
            variable=self.clone_limit, command=self.toggle_clones)
        list_label = ctk.CTkLabel(limits_frame, text="List Limit:")
        self.list_spin = ctk.CTkEntry(
            limits_frame, width=100,
            textvariable=self.max_list)
        list_check = ctk.CTkCheckBox(
            limits_frame, text="Enable?",
            variable=self.list_limit, command=self.toggle_list)

        self.turbo_hotkey = ctk.BooleanVar(app, name="TURBO_HOTKEY")
        self.fullscreen_hotkey = ctk.BooleanVar(app, name="FULLSCREEN_HOTKEY")
        self.debug_hotkeys = ctk.BooleanVar(app, name="DEBUG_HOTKEYS")

        ctk.CTkLabel(hotkey_frame, text="Hotkeys", font=("", 12, "bold")).grid(row=0, column=0, sticky="w", padx=10, pady=5)
        turbo_hk_check = ctk.CTkCheckBox(
            hotkey_frame, text="Turbo Hotkey (F10)",
            variable=self.turbo_hotkey)
        fullscreen_check = ctk.CTkCheckBox(
            hotkey_frame, text="Fullscreen Hotkey (F11)",
            variable=self.fullscreen_hotkey)
        debug_check = ctk.CTkCheckBox(
            hotkey_frame, text="Debug Hotkeys (F3 + F,R,S,P)",
            variable=self.debug_hotkeys)

        self.username = ctk.StringVar(app, name="USERNAME")
        self.draw_fps = ctk.BooleanVar(app, name="DRAW_FPS")
        self.random_seed = ctk.IntVar(app, name="RANDOM_SEED")

        ctk.CTkLabel(misc_frame, text="Miscellaneous", font=("", 12, "bold")).grid(row=0, column=0, sticky="w", padx=10, pady=5)
        username_label = ctk.CTkLabel(misc_frame, text="Username:")
        username_box = ctk.CTkEntry(misc_frame, textvariable=self.username)
        random_label = ctk.CTkLabel(misc_frame, text="Random Seed:")
        random_spin = ctk.CTkEntry(
            misc_frame, width=70,
            textvariable=self.random_seed)
        fps_check = ctk.CTkCheckBox(
            misc_frame, text="Draw FPS",
            variable=self.draw_fps)

        fps_label.grid(column=0, row=0, sticky="W")
        fps_spin.grid(column=2, row=0, sticky="W", padx=3, pady=3)
        turbo_check.grid(column=3, row=0, sticky="W", padx=3)
        warp_label.grid(column=0, row=1, sticky="W")
        warp_spin.grid(column=2, row=1, sticky="W", padx=3, pady=3)
        work_label.grid(column=0, row=2, sticky="W")
        work_spin.grid(column=2, row=2, sticky="W", padx=3, pady=3)

        stage_label.grid(column=0, row=0, sticky="W")
        stagew_spin.grid(column=1, row=0, sticky="W",
                         padx=3, pady=3, columnspan=2)
        stageh_spin.grid(column=3, row=0, sticky="W", padx=3, pady=3)
        display_label.grid(column=0, row=1, sticky="W")
        displayw_spin.grid(column=1, row=1, sticky="W",
                           padx=3, pady=3, columnspan=2)
        displayh_spin.grid(column=3, row=1, sticky="W", padx=3, pady=3)
        resize_check.grid(column=0, row=2, sticky="W", columnspan=2)
        scaled_check.grid(column=0, row=3, sticky="W", columnspan=2)
        fs_label.grid(column=0, row=4, sticky="W", columnspan=2)
        fs_spin.grid(column=2, row=4, sticky="W", padx=3, pady=3, columnspan=2)
        scaled_check.configure(state="disabled")

        title_label.grid(column=0, row=0, sticky="W")
        title_box.grid(column=1, row=0, sticky="EW", padx=3, pady=3)
        title_check.grid(column=0, row=1, sticky="W", columnspan=2)

        channels_label.grid(column=0, row=0, sticky="W")
        channels_spin.grid(column=1, row=0, sticky="W", padx=3, pady=3)
        volume_label.grid(column=0, row=1, sticky="W")
        volume_spin.grid(column=1, row=1, sticky="W", padx=3, pady=3)

        clones_label.grid(column=0, row=0, sticky="W")
        self.clones_spin.grid(column=1, row=0, sticky="W", padx=3, pady=3)
        clones_check.grid(column=2, row=0, sticky="W", padx=3)
        list_label.grid(column=0, row=1, sticky="W")
        self.list_spin.grid(column=1, row=1, sticky="W", padx=3, pady=3)
        list_check.grid(column=2, row=1, sticky="W", padx=3)

        turbo_hk_check.grid(column=0, row=0, sticky="W")
        fullscreen_check.grid(column=0, row=1, sticky="W")
        debug_check.grid(column=0, row=2, sticky="W")

        username_label.grid(column=0, row=0, sticky="W")
        username_box.grid(column=1, row=0, sticky="EW", padx=3, pady=3)
        random_label.grid(column=0, row=1, sticky="W")
        random_spin.grid(column=1, row=1, sticky="W", padx=3, pady=3)
        fps_check.grid(column=0, row=2, sticky="W", columnspan=2)

        timing_frame.grid(column=0, row=0, sticky="NSEW", padx=10, pady=5)
        display_frame.grid(column=1, row=0, sticky="NSEW", padx=10, pady=5, rowspan=2)
        title_frame.grid(column=0, row=1, sticky="NSEW", padx=10, pady=5)
        audio_frame.grid(column=0, row=3, sticky="NSEW", padx=10, pady=5)
        limits_frame.grid(column=1, row=3, sticky="NSEW", padx=10, pady=5)
        hotkey_frame.grid(column=0, row=4, sticky="NSEW", padx=10, pady=5)
        misc_frame.grid(column=1, row=4, sticky="NSEW", padx=10, pady=5)

        timing_frame.columnconfigure(3, weight=1)
        display_frame.columnconfigure(4, weight=1)
        title_frame.columnconfigure(1, weight=1)
        audio_frame.columnconfigure(1, weight=1)
        limits_frame.columnconfigure(2, weight=1)
        hotkey_frame.columnconfigure(1, weight=1)
        misc_frame.columnconfigure(1, weight=1)

        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)

    def toggle_clones(self):
        """Toggles the clone limit"""
        if self.clone_limit.get():
            self.max_clones.set(config.project.MAX_CLONES)
            self.clones_spin.configure(state="normal")
        else:
            self.max_clones.set(0)
            self.clones_spin.configure(state="disabled")

    def toggle_list(self):
        """Toggles the clone limit"""
        if self.list_limit.get():
            self.max_list.set(config.project.MAX_LIST)
            self.list_spin.configure(state="normal")
        else:
            self.max_list.set(0)
            self.list_spin.configure(state="disabled")

    def switch(self):
        """Called when the tab is switched to"""
        if self.max_list.get():
            self.list_spin.configure(state="normal")
        else:
            self.list_spin.configure(state="disabled")

        if self.max_clones.get():
            self.clones_spin.configure(state="normal")
        else:
            self.clones_spin.configure(state="disabled")


class DebugFrame(ctk.CTkFrame):
    """Handles the Debug tab of settings"""

    def __init__(self, app, parent, **kwargs):
        super().__init__(parent, **kwargs, fg_color="transparent")
        self.app = app

        debug_frame = style.section(self)
        log_frame = style.section(self)

        self.debug_json = ctk.BooleanVar(app, name="DEBUG_JSON")
        self.format_json = ctk.BooleanVar(app, name="FORMAT_JSON")
        self.overwrite_engine = ctk.BooleanVar(app, name="OVERWRITE_ENGINE")

        ctk.CTkLabel(debug_frame, text="Debug", font=("", 12, "bold")).grid(row=0, column=0, sticky="w", padx=10, pady=5)
        d_json_check = ctk.CTkCheckBox(
            debug_frame, text="Save project.json",
            variable=self.debug_json, command=self.json_toggle)
        self.f_json_check = ctk.CTkCheckBox(
            debug_frame, text="Format project.json",
            variable=self.format_json)
        engine_check = ctk.CTkCheckBox(
            debug_frame, text="Overwrite Engine",
            variable=self.overwrite_engine)

        self.log_level = ctk.StringVar(app, name="LOG_LEVEL")
        self.log_path = ctk.StringVar(app, name="LOG_PATH")
        self.save_log = ctk.StringVar(app, name="SAVE_LOG")

        ctk.CTkLabel(log_frame, text="Logging", font=("", 12, "bold")).grid(row=0, column=0, sticky="w", padx=10, pady=5)
        level_label = ctk.CTkLabel(log_frame, text="Log Level:")
        level_spin = ctk.CTkEntry(log_frame, width=70,
                                 textvariable=self.log_level)
        path_label = ctk.CTkLabel(log_frame, text="Log Path:")
        path_box = ctk.CTkEntry(
            log_frame, textvariable=self.log_path, state="disabled")
        save_box = ctk.CTkCheckBox(log_frame, text="Save Log", state="disabled",
                                   variable=self.save_log)

        d_json_check.grid(column=0, row=1, sticky="W", padx=10)
        self.f_json_check.grid(column=0, row=2, sticky="W", padx=10)
        engine_check.grid(column=0, row=3, sticky="W", padx=10, pady=(0, 10))

        level_label.grid(column=0, row=1, sticky="W", padx=10)
        level_spin.grid(column=1, row=1, sticky="W", padx=3, pady=3)
        path_label.grid(column=0, row=2, sticky="W", padx=10)
        path_box.grid(column=1, row=2, sticky="EW", padx=3, pady=3)
        save_box.grid(column=0, row=3, sticky="W", padx=10, pady=(0, 10))

        debug_frame.grid(column=0, row=0, sticky="NSEW", padx=10, pady=5)
        debug_frame.columnconfigure(0, weight=1)

        log_frame.grid(column=0, row=1, sticky="NSEW", padx=10, pady=5)
        log_frame.columnconfigure(1, weight=1)

        self.columnconfigure(0, weight=1)

        self.json_toggle()

    def json_toggle(self):
        """Called when save project.json is toggled"""
        if self.debug_json.get():
            self.f_json_check.configure(state="normal")
        else:
            self.f_json_check.configure(state="disabled")

    def switch(self):
        """Called when this tab is shown"""
        self.json_toggle()
