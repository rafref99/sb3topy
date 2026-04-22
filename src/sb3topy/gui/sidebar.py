"""
toolbox.py

Contains miscellaneous custom components used by the gui app
"""

# pylint: disable=too-many-ancestors

import customtkinter as ctk


class FlatRadio(ctk.CTkButton):
    """A custom flat radio button using CTkButton"""

    def __init__(self, parent, text, variable, **kwargs):
        super().__init__(
            parent, text=text,
            corner_radius=0,
            fg_color="transparent",
            text_color=("gray10", "gray90"),
            hover_color=("gray70", "gray30"),
            font=("TkMenuFont", 14),
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
            self.configure(fg_color=("gray75", "gray25"))
        else:
            self.configure(fg_color="transparent")


class Sidebar(ctk.CTkFrame):
    """Handles the sidebar on the left and frames put in it"""

    def __init__(self, root, variable):
        super().__init__(root, corner_radius=0)

        convert_button = FlatRadio(self, "Convert", variable=variable)
        examples_button = FlatRadio(self, "Examples", variable=variable)
        output_button = FlatRadio(self, "Output", variable=variable)
        settings_button = FlatRadio(self, "Settings", variable=variable)

        convert_button.grid(column=0, row=0, sticky="ew", padx=5, pady=2)
        examples_button.grid(column=0, row=1, sticky="ew", padx=5, pady=2)
        output_button.grid(column=0, row=2, sticky="ew", padx=5, pady=2)
        settings_button.grid(column=0, row=3, sticky="ew", padx=5, pady=2)

        self.columnconfigure(0, weight=1)
