"""
toolbox.py

Contains miscellaneous custom components used by the gui app
"""

# pylint: disable=too-many-ancestors

import customtkinter as ctk

from . import style


class FlatRadio(ctk.CTkButton):
    """A custom flat radio button using CTkButton"""

    def __init__(self, parent, text, variable, **kwargs):
        super().__init__(
            parent, text=text,
            corner_radius=8,
            fg_color="transparent",
            text_color=style.TEXT,
            hover_color=style.ACCENT_ACTIVE_HOVER,
            font=("TkMenuFont", 13, "bold"),
            height=38,
            anchor="w",
            command=self.mouse_click,
            **kwargs)
        self.value = text.lower()
        self.variable = variable

        variable.trace_add("write", self.cb_variable)
        self.cb_variable()

    def mouse_click(self):
        """Called when the button is clicked"""
        self.variable.set(self.value)

    def cb_variable(self, *args):
        """Called when the variable is updated"""
        if self.variable.get() == self.value:
            self.configure(
                fg_color=style.ACCENT,
                hover_color=style.ACCENT_ACTIVE_HOVER,
                text_color="#ffffff")
        else:
            self.configure(
                fg_color="transparent",
                hover_color=style.SURFACE_ALT,
                text_color=style.TEXT)


class Sidebar(ctk.CTkFrame):
    """Handles the sidebar on the left and frames put in it"""

    def __init__(self, root, variable):
        super().__init__(root, corner_radius=0, fg_color=style.SIDEBAR)

        brand = ctk.CTkLabel(
            self, text="sb3topy", font=("TkDefaultFont", 20, "bold"),
            text_color=style.TEXT, anchor="w")
        subtitle = ctk.CTkLabel(
            self, text="Scratch to Python", font=style.FONT_BODY,
            text_color=style.MUTED, anchor="w")

        convert_button = FlatRadio(self, "Convert", variable=variable)
        examples_button = FlatRadio(self, "Examples", variable=variable)
        output_button = FlatRadio(self, "Output", variable=variable)
        settings_button = FlatRadio(self, "Settings", variable=variable)

        brand.grid(column=0, row=0, sticky="ew", padx=18, pady=(22, 0))
        subtitle.grid(column=0, row=1, sticky="ew", padx=18, pady=(0, 22))

        convert_button.grid(column=0, row=2, sticky="ew", padx=10, pady=3)
        examples_button.grid(column=0, row=3, sticky="ew", padx=10, pady=3)
        output_button.grid(column=0, row=4, sticky="ew", padx=10, pady=3)
        settings_button.grid(column=0, row=5, sticky="ew", padx=10, pady=3)

        self.columnconfigure(0, weight=1)
