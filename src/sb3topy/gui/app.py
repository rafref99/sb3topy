"""
app.py

Contains the gui app

TODO export config
"""

# from ctypes import windll
from pathlib import Path

import customtkinter as ctk

from .. import config, main
from .convert import ConvertFrame
from .examples import ExamplesFrame
from .output import OutputFrame
from .settings import SettingsFrame
from .sidebar import Sidebar
from . import style

# windll.shcore.SetProcessDpiAwareness(True)
ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

try:
    from tkinterdnd2 import TkinterDnD
except ImportError:
    _BaseWindow = ctk.CTk
    DRAG_DROP_AVAILABLE = False
else:
    class _BaseWindow(ctk.CTk, TkinterDnD.DnDWrapper):
        """CustomTkinter root with optional native file drop support."""

        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.TkdndVersion = TkinterDnD._require(self)

    DRAG_DROP_AVAILABLE = True


def run_app():
    """Runs the GUI App"""
    App().mainloop()


class App(_BaseWindow):
    """Main App class"""

    def __init__(self):
        super().__init__()
        style.apply_window(self)
        self._apply_icon()
        self.scale = 1.0

        # Create config variables
        self.init_config()
        self.read_config()

        self.mode = ctk.StringVar()
        self.mode.trace_add('write', self.cb_mode)

        sidebar = Sidebar(self, self.mode)
        self.convert = ConvertFrame(self)
        self.examples = ExamplesFrame(self)
        self.output = OutputFrame(self)
        self.settings = SettingsFrame(self)

        sidebar.grid(column=0, row=0, sticky="NSEW")
        self.convert.grid(column=1, row=0, sticky="NSWE")
        self.examples.grid(column=1, row=0, sticky="NSEW")
        self.output.grid(column=1, row=0, sticky="NSWE")
        self.settings.grid(column=1, row=0, sticky="NSWE")

        self.columnconfigure(0, minsize=170)
        self.columnconfigure(1, minsize=300, weight=1)
        self.rowconfigure(0, minsize=300, weight=1)

        self.mode.set(config.DEFAULT_GUI_TAB)

        # config.config.set_all(1)
        # self.read_config()

    def _apply_icon(self):
        """Set the window icon from the repo root icon asset."""
        icon_path = Path(__file__).resolve().parents[3] / "icon.png"
        if not icon_path.is_file():
            return

        try:
            import tkinter as tk
            self._window_icon = tk.PhotoImage(file=str(icon_path))
            self.iconphoto(True, self._window_icon)
        except Exception:
            pass

    def cb_mode(self, *_):
        """Called when the mode switches"""
        self.convert.grid_remove()
        self.examples.grid_remove()
        self.output.grid_remove()
        self.settings.grid_remove()

        mode = self.mode.get()
        if mode == "convert":
            self.convert.grid()
        elif mode == "examples":
            self.examples.grid()
            self.examples.switch_to()
        elif mode == "output":
            self.output.grid()
            self.output.switch_to()
        elif mode == "settings":
            self.settings.grid()

    def init_config(self):
        """Creates config variables"""
        # Unsorted
        ctk.BooleanVar(self, name="AUTORUN")
        ctk.Variable(self, name="JSON_SHA")
        ctk.BooleanVar(self, name="CONVERT_ASSETS")
        ctk.BooleanVar(self, name="PARSE_PROJECT")
        ctk.BooleanVar(self, name="COPY_ENGINE")
        ctk.StringVar(self, name="CONFIG_PATH")
        ctk.BooleanVar(self, name="AUTOLOAD_CONFIG")

        # General / Paths
        ctk.StringVar(self, name="OUTPUT_PATH")
        ctk.StringVar(self, name="PROJECT_PATH")
        ctk.StringVar(self, name="PROJECT_URL")

        # Assets / Extraction
        ctk.BooleanVar(self, name="VERIFY_ASSETS")
        ctk.BooleanVar(self, name="FRESHEN_ASSETS")
        ctk.BooleanVar(self, name="RECONVERT_SOUNDS")
        ctk.BooleanVar(self, name="RECONVERT_IMAGES")

        # Assets / Workers
        ctk.IntVar(self, name="DOWNLOAD_THREADS")
        ctk.IntVar(self, name="CONVERT_THREADS")
        ctk.IntVar(self, name="CONVERT_TIMEOUT")

        # Assets / SVGs
        ctk.BooleanVar(self, name="USE_SVG_CMD")
        ctk.StringVar(self, name="SVG_COMMAND")
        ctk.IntVar(self, name="SVG_SCALE")
        # ctk.IntVar(self, name="SVG_DPI")
        ctk.BooleanVar(self, name="CONVERT_COSTUMES")

        # Assets / MP3s
        ctk.BooleanVar(self, name="CONVERT_SOUNDS")
        ctk.StringVar(self, name="MP3_COMMAND")

        # Optimizations / Basic
        ctk.BooleanVar(self, name="LEGACY_LISTS")
        ctk.BooleanVar(self, name="VAR_TYPES")
        ctk.BooleanVar(self, name="ARG_TYPES")
        ctk.BooleanVar(self, name="LIST_TYPES")

        # Optimizations / Advanced
        ctk.BooleanVar(self, name="DISABLE_ANY_CAST")
        ctk.BooleanVar(self, name="AGGRESSIVE_NUM_CAST")
        ctk.BooleanVar(self, name="CHANGED_NUM_CAST")
        ctk.BooleanVar(self, name="DISABLE_STR_CAST")
        ctk.BooleanVar(self, name="DISABLE_INT_CAST")

        # Project / Timings
        ctk.IntVar(self, name="TARGET_FPS")
        ctk.BooleanVar(self, name="TURBO_MODE")
        ctk.IntVar(self, name="WORK_TIME_INV")
        ctk.DoubleVar(self, name="WARP_TIME")

        # Project / Display
        ctk.IntVar(self, name="STAGE_WIDTH")
        ctk.IntVar(self, name="STAGE_HEIGHT")
        ctk.IntVar(self, name="DISPLAY_WIDTH")
        ctk.IntVar(self, name="DISPLAY_HEIGHT")
        ctk.BooleanVar(self, name="ALLOW_RESIZE")
        ctk.BooleanVar(self, name="SCALED_DISPLAY")
        ctk.IntVar(self, name="FS_SCALE")

        # Project / Title
        ctk.BooleanVar(self, name="DYNAMIC_TITLE")
        ctk.StringVar(self, name="TITLE")

        # Project / Audio
        ctk.IntVar(self, name="AUDIO_CHANNELS")
        ctk.IntVar(self, name="MASTER_VOLUME")

        # Project / Limits
        ctk.IntVar(self, name="MAX_CLONES")
        ctk.IntVar(self, name="MAX_LIST")

        # Project / Hotkeys
        ctk.BooleanVar(self, name="TURBO_HOTKEY")
        ctk.BooleanVar(self, name="FULLSCREEN_HOTKEY")
        ctk.BooleanVar(self, name="DEBUG_HOTKEYS")

        # Project / Miscellaneous
        ctk.BooleanVar(self, name="DRAW_FPS")
        ctk.StringVar(self, name="USERNAME")
        ctk.IntVar(self, name="RANDOM_SEED")

        # Debug / Debug
        ctk.IntVar(self, name="LOG_LEVEL")
        ctk.BooleanVar(self, name="DEBUG_JSON")
        ctk.BooleanVar(self, name="FORMAT_JSON")
        ctk.BooleanVar(self, name="OVERWRITE_ENGINE")

    def run_main(self):
        """Runs the converter with the current config"""
        self.mode.set("output")
        process, queue = main.run_mp()
        self.output.start_watching(process, queue)

    def read_config(self):
        """
        Loads values from the config module into variables of this Tk.

        re.sub('tk.+name="(.+)"', r'self.setvar("\1", config.\1)', text)
        """
        # Unsorted
        self.setvar("AUTORUN", config.AUTORUN)
        self.setvar("JSON_SHA", config.JSON_SHA)
        self.setvar("CONVERT_ASSETS", config.CONVERT_ASSETS)
        self.setvar("PARSE_PROJECT", config.PARSE_PROJECT)
        self.setvar("COPY_ENGINE", config.COPY_ENGINE)
        self.setvar("CONFIG_PATH", config.CONFIG_PATH)
        self.setvar("AUTOLOAD_CONFIG", config.AUTOLOAD_CONFIG)

        # General / Paths
        self.setvar("OUTPUT_PATH", config.OUTPUT_PATH)
        self.setvar("PROJECT_PATH", config.PROJECT_PATH)
        self.setvar("PROJECT_URL", config.PROJECT_URL)

        # Assets / Extraction
        self.setvar("VERIFY_ASSETS", config.VERIFY_ASSETS)
        self.setvar("FRESHEN_ASSETS", config.FRESHEN_ASSETS)
        self.setvar("RECONVERT_SOUNDS", config.RECONVERT_SOUNDS)
        self.setvar("RECONVERT_IMAGES", config.RECONVERT_IMAGES)

        # Assets / Workers
        self.setvar("DOWNLOAD_THREADS", config.DOWNLOAD_THREADS)
        self.setvar("CONVERT_THREADS", config.CONVERT_THREADS)
        self.setvar("CONVERT_TIMEOUT", config.CONVERT_TIMEOUT)

        # Assets / SVGs
        self.setvar("USE_SVG_CMD", config.USE_SVG_CMD)
        self.setvar("SVG_COMMAND", config.SVG_COMMAND)
        self.setvar("SVG_SCALE", config.SVG_SCALE)
        # self.setvar("SVG_DPI", config.SVG_DPI)
        self.setvar("CONVERT_COSTUMES", config.CONVERT_COSTUMES)

        # Assets / MP3s
        self.setvar("CONVERT_SOUNDS", config.CONVERT_SOUNDS)
        self.setvar("MP3_COMMAND", config.MP3_COMMAND)

        # Optimizations / Basic
        self.setvar("LEGACY_LISTS", config.LEGACY_LISTS)
        self.setvar("VAR_TYPES", config.VAR_TYPES)
        self.setvar("ARG_TYPES", config.ARG_TYPES)
        self.setvar("LIST_TYPES", config.LIST_TYPES)
        self.setvar("SOLO_BROADCASTS", config.SOLO_BROADCASTS)
        self.setvar("WARP_ALL", config.WARP_ALL)

        # Optimizations / Advanced
        self.setvar("DISABLE_ANY_CAST", config.DISABLE_ANY_CAST)
        self.setvar("AGGRESSIVE_NUM_CAST", config.AGGRESSIVE_NUM_CAST)
        self.setvar("CHANGED_NUM_CAST", config.CHANGED_NUM_CAST)
        self.setvar("DISABLE_STR_CAST", config.DISABLE_STR_CAST)
        self.setvar("DISABLE_INT_CAST", config.DISABLE_INT_CAST)

        # Project / Timings
        self.setvar("TARGET_FPS", config.TARGET_FPS)
        self.setvar("TURBO_MODE", config.TURBO_MODE)
        self.setvar("WORK_TIME_INV", config.WORK_TIME_INV)
        self.setvar("WARP_TIME", config.WARP_TIME)

        # Project / Display
        self.setvar("STAGE_WIDTH", config.STAGE_WIDTH)
        self.setvar("STAGE_HEIGHT", config.STAGE_HEIGHT)
        self.setvar("DISPLAY_WIDTH", config.DISPLAY_WIDTH)
        self.setvar("DISPLAY_HEIGHT", config.DISPLAY_HEIGHT)
        self.setvar("ALLOW_RESIZE", config.ALLOW_RESIZE)
        self.setvar("SCALED_DISPLAY", config.SCALED_DISPLAY)
        self.setvar("FS_SCALE", config.FS_SCALE)

        # Project / Title
        self.setvar("DYNAMIC_TITLE", config.DYNAMIC_TITLE)
        self.setvar("TITLE", config.TITLE)

        # Project / Audio
        self.setvar("AUDIO_CHANNELS", config.AUDIO_CHANNELS)
        self.setvar("MASTER_VOLUME", config.MASTER_VOLUME * 100)

        # Project / Limits
        self.setvar("MAX_CLONES", config.MAX_CLONES)
        self.setvar("MAX_LIST", config.MAX_LIST)

        # Project / Hotkeys
        self.setvar("TURBO_HOTKEY", config.TURBO_HOTKEY)
        self.setvar("FULLSCREEN_HOTKEY", config.FULLSCREEN_HOTKEY)
        self.setvar("DEBUG_HOTKEYS", config.DEBUG_HOTKEYS)

        # Project / Miscellaneous
        self.setvar("DRAW_FPS", config.DRAW_FPS)
        self.setvar("USERNAME", config.USERNAME)
        self.setvar("RANDOM_SEED", config.RANDOM_SEED)

        # Debug / Debug
        self.setvar("LOG_LEVEL", config.LOG_LEVEL)
        self.setvar("DEBUG_JSON", config.DEBUG_JSON)
        self.setvar("FORMAT_JSON", config.FORMAT_JSON)
        self.setvar("OVERWRITE_ENGINE", config.OVERWRITE_ENGINE)

    def write_config(self):
        """
        Writes values from variables of this Tk to the config module.

        re.sub('tk.+name="(.+)".+', r'self.setvar("\1", config.\1)', text)
        """
        # Unsorted
        config.AUTORUN = tkbool(self.getvar("AUTORUN"))
        config.JSON_SHA = self.getvar("JSON_SHA")
        config.CONVERT_ASSETS = tkbool(self.getvar("CONVERT_ASSETS"))
        config.PARSE_PROJECT = tkbool(self.getvar("PARSE_PROJECT"))
        config.COPY_ENGINE = tkbool(self.getvar("COPY_ENGINE"))
        config.CONFIG_PATH = self.getvar("CONFIG_PATH")
        config.AUTOLOAD_CONFIG = tkbool(self.getvar("AUTOLOAD_CONFIG"))

        # General / Paths
        config.OUTPUT_PATH = self.getvar("OUTPUT_PATH")
        config.PROJECT_PATH = self.getvar("PROJECT_PATH")
        config.PROJECT_URL = self.getvar("PROJECT_URL")

        # Assets / Extraction
        config.VERIFY_ASSETS = tkbool(self.getvar("VERIFY_ASSETS"))
        config.FRESHEN_ASSETS = tkbool(self.getvar("FRESHEN_ASSETS"))
        config.RECONVERT_SOUNDS = tkbool(self.getvar("RECONVERT_SOUNDS"))
        config.RECONVERT_IMAGES = tkbool(self.getvar("RECONVERT_IMAGES"))

        # Assets / Workers
        config.DOWNLOAD_THREADS = self.getvar("DOWNLOAD_THREADS")
        config.CONVERT_THREADS = self.getvar("CONVERT_THREADS")
        config.CONVERT_TIMEOUT = self.getvar("CONVERT_TIMEOUT")

        # Assets / SVGs
        config.USE_SVG_CMD = tkbool(self.getvar("USE_SVG_CMD"))
        config.SVG_COMMAND = self.getvar("SVG_COMMAND")
        config.SVG_SCALE = self.getvar("SVG_SCALE")
        # config.SVG_DPI = self.getvar("SVG_DPI")
        config.CONVERT_COSTUMES = tkbool(self.getvar("CONVERT_COSTUMES"))

        # Assets / MP3s
        config.CONVERT_SOUNDS = tkbool(self.getvar("CONVERT_SOUNDS"))
        config.MP3_COMMAND = self.getvar("MP3_COMMAND")

        # Optimizations / Basic
        config.LEGACY_LISTS = tkbool(self.getvar("LEGACY_LISTS"))
        config.VAR_TYPES = tkbool(self.getvar("VAR_TYPES"))
        config.ARG_TYPES = tkbool(self.getvar("ARG_TYPES"))
        config.LIST_TYPES = tkbool(self.getvar("LIST_TYPES"))
        config.SOLO_BROADCASTS = tkbool(self.getvar("SOLO_BROADCASTS"))
        config.WARP_ALL = tkbool(self.getvar("WARP_ALL"))

        # Optimizations / Advanced
        config.DISABLE_ANY_CAST = tkbool(self.getvar("DISABLE_ANY_CAST"))
        config.AGGRESSIVE_NUM_CAST = tkbool(self.getvar("AGGRESSIVE_NUM_CAST"))
        config.CHANGED_NUM_CAST = tkbool(self.getvar("CHANGED_NUM_CAST"))
        config.DISABLE_STR_CAST = tkbool(self.getvar("DISABLE_STR_CAST"))
        config.DISABLE_INT_CAST = tkbool(self.getvar("DISABLE_INT_CAST"))

        # Project / Timings
        config.TARGET_FPS = self.getvar("TARGET_FPS")
        config.TURBO_MODE = tkbool(self.getvar("TURBO_MODE"))
        config.WORK_TIME_INV = self.getvar("WORK_TIME_INV")
        config.WARP_TIME = self.getvar("WARP_TIME")

        # Project / Display
        config.STAGE_WIDTH = self.getvar("STAGE_WIDTH")
        config.STAGE_HEIGHT = self.getvar("STAGE_HEIGHT")
        config.DISPLAY_WIDTH = self.getvar("DISPLAY_WIDTH")
        config.DISPLAY_HEIGHT = self.getvar("DISPLAY_HEIGHT")
        config.ALLOW_RESIZE = tkbool(self.getvar("ALLOW_RESIZE"))
        config.SCALED_DISPLAY = tkbool(self.getvar("SCALED_DISPLAY"))
        config.FS_SCALE = self.getvar("FS_SCALE")

        # Project / Title
        config.DYNAMIC_TITLE = tkbool(self.getvar("DYNAMIC_TITLE"))
        config.TITLE = self.getvar("TITLE")

        # Project / Audio
        config.AUDIO_CHANNELS = self.getvar("AUDIO_CHANNELS")
        config.MASTER_VOLUME = int(self.getvar("MASTER_VOLUME")) / 100

        # Project / Limits
        config.MAX_CLONES = self.getvar("MAX_CLONES")
        config.MAX_LIST = self.getvar("MAX_LIST")

        # Project / Hotkeys
        config.TURBO_HOTKEY = tkbool(self.getvar("TURBO_HOTKEY"))
        config.FULLSCREEN_HOTKEY = tkbool(self.getvar("FULLSCREEN_HOTKEY"))
        config.DEBUG_HOTKEYS = tkbool(self.getvar("DEBUG_HOTKEYS"))

        # Project / Miscellaneous
        config.USERNAME = self.getvar("USERNAME")
        config.RANDOM_SEED = self.getvar("RANDOM_SEED")

        # Debug / Debug
        config.LOG_LEVEL = int(self.getvar("LOG_LEVEL"))
        config.DEBUG_JSON = tkbool(self.getvar("DEBUG_JSON"))
        config.FORMAT_JSON = tkbool(self.getvar("FORMAT_JSON"))
        config.OVERWRITE_ENGINE = tkbool(self.getvar("OVERWRITE_ENGINE"))


def tkbool(value):
    """
    False for '0' and falsey values, otherwise true

    tk checkboxes use '1' and '0' for True and False
    """
    return False if value == '0' else bool(value)
