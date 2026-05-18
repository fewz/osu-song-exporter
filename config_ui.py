# config_ui.py

import json
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import ttk

CONFIG_FILE = "config.json"

DEFAULT_CONFIG = {
    "OSU_SONGS_FOLDER": "",
    "EXPORT_FOLDER": "",
    "LIMIT_ALL": True,
    "LIMIT": 10,
    "COPY_MODE": True,
    "EXPORT_BACKGROUND": True,
    "GENERATE_PLAYLIST": False,
    "REFRESH_DATABASE": False,
    "MAX_WORKERS": 8
}


class ConfigUI:

    def __init__(self, root):

        self.root = root

        self.root.title("osu! Song Exporter Config")
        self.root.geometry("610x750")
        self.root.minsize(610,750)

        self.config = self.load_config()

        self.build_ui()

    # =====================================================
    # CONFIG
    # =====================================================

    def load_config(self):

        config_path = Path(CONFIG_FILE)

        if not config_path.exists():
            return DEFAULT_CONFIG.copy()

        try:

            with open(config_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            result = DEFAULT_CONFIG.copy()
            result.update(data)

            return result

        except:
            return DEFAULT_CONFIG.copy()

    def save_config(self):

        config = {
            "OSU_SONGS_FOLDER": self.osu_folder_var.get().strip(),
            "EXPORT_FOLDER": self.export_folder_var.get().strip(),
            "LIMIT_ALL": self.limit_all_var.get(),
            "LIMIT": int(self.limit_var.get()),
            "COPY_MODE": self.copy_mode_var.get(),
            "EXPORT_BACKGROUND": self.export_bg_var.get(),
            "GENERATE_PLAYLIST": self.playlist_var.get(),
            "REFRESH_DATABASE": self.refresh_db_var.get(),
            "MAX_WORKERS": int(self.max_workers_var.get())
        }

        # =============================================
        # VALIDATION
        # =============================================

        if not config["OSU_SONGS_FOLDER"]:

            messagebox.showerror(
                "Missing osu Folder",
                "Please select osu! Songs folder."
            )

            return

        if not Path(config["OSU_SONGS_FOLDER"]).exists():

            messagebox.showerror(
                "Invalid Path",
                "osu! Songs folder does not exist."
            )

            return

        if not config["EXPORT_FOLDER"]:

            messagebox.showerror(
                "Missing Export Folder",
                "Please select export folder."
            )

            return

        if not config["LIMIT_ALL"]:

            if config["LIMIT"] <= 0:

                messagebox.showerror(
                    "Invalid Limit",
                    "Limit must be greater than 0."
                )

                return

        if config["MAX_WORKERS"] <= 0:

            messagebox.showerror(
                "Invalid Worker Count",
                "Max workers must be greater than 0."
            )

            return

        with open(CONFIG_FILE, "w", encoding="utf-8") as f:

            json.dump(
                config,
                f,
                ensure_ascii=False,
                indent=4
            )

        messagebox.showinfo(
            "Saved",
            "Configuration saved successfully."
        )

    # =====================================================
    # UI
    # =====================================================

    def build_ui(self):

        style = ttk.Style()

        try:
            style.theme_use("clam")
        except:
            pass

        # =================================================
        # SCROLLABLE ROOT
        # =================================================

        container = ttk.Frame(self.root)
        container.pack(fill="both", expand=True)

        canvas = tk.Canvas(
            container,
            highlightthickness=0
        )

        scrollbar = ttk.Scrollbar(
            container,
            orient="vertical",
            command=canvas.yview
        )

        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(
                scrollregion=canvas.bbox("all")
            )
        )

        canvas.create_window(
            (0, 0),
            window=scrollable_frame,
            anchor="nw"
        )

        canvas.configure(
            yscrollcommand=scrollbar.set
        )

        canvas.pack(
            side="left",
            fill="both",
            expand=True
        )

        scrollbar.pack(
            side="right",
            fill="y"
        )

        # Mouse wheel

        def _on_mousewheel(event):

            canvas.yview_scroll(
                int(-1 * (event.delta / 120)),
                "units"
            )

        canvas.bind_all(
            "<MouseWheel>",
            _on_mousewheel
        )

        # =================================================
        # MAIN
        # =================================================

        main = ttk.Frame(
            scrollable_frame,
            padding=20
        )

        main.pack(fill="both", expand=True)

        title = ttk.Label(
            main,
            text="osu! Song Exporter",
            font=("Segoe UI", 22, "bold")
        )

        title.pack(anchor="w")

        subtitle = ttk.Label(
            main,
            text="Configuration Panel",
            font=("Segoe UI", 10)
        )

        subtitle.pack(anchor="w", pady=(0, 20))

        # =================================================
        # PATHS
        # =================================================

        paths_frame = ttk.LabelFrame(
            main,
            text="Folders",
            padding=16
        )

        paths_frame.pack(fill="x", pady=(0, 16))

        self.osu_folder_var = tk.StringVar(
            value=self.config["OSU_SONGS_FOLDER"]
        )

        ttk.Label(
            paths_frame,
            text="osu! Songs Folder"
        ).grid(row=0, column=0, sticky="w")

        ttk.Entry(
            paths_frame,
            textvariable=self.osu_folder_var,
            width=70
        ).grid(row=1, column=0, padx=(0, 10), pady=(4, 12))

        ttk.Button(
            paths_frame,
            text="Browse",
            command=self.pick_osu_folder
        ).grid(row=1, column=1)

        self.export_folder_var = tk.StringVar(
            value=self.config["EXPORT_FOLDER"]
        )

        ttk.Label(
            paths_frame,
            text="Export Folder"
        ).grid(row=2, column=0, sticky="w")

        ttk.Entry(
            paths_frame,
            textvariable=self.export_folder_var,
            width=70
        ).grid(row=3, column=0, padx=(0, 10), pady=(4, 0))

        ttk.Button(
            paths_frame,
            text="Browse",
            command=self.pick_export_folder
        ).grid(row=3, column=1)

        # =================================================
        # SETTINGS
        # =================================================

        settings_frame = ttk.LabelFrame(
            main,
            text="Settings",
            padding=16
        )

        settings_frame.pack(fill="x", pady=(0, 16))

        self.copy_mode_var = tk.BooleanVar(
            value=self.config["COPY_MODE"]
        )

        self.export_bg_var = tk.BooleanVar(
            value=self.config["EXPORT_BACKGROUND"]
        )

        self.playlist_var = tk.BooleanVar(
            value=self.config["GENERATE_PLAYLIST"]
        )

        self.refresh_db_var = tk.BooleanVar(
            value=self.config["REFRESH_DATABASE"]
        )

        ttk.Checkbutton(
            settings_frame,
            text="Copy Mode",
            variable=self.copy_mode_var
        ).pack(anchor="w")

        ttk.Checkbutton(
            settings_frame,
            text="Export Background / Cover",
            variable=self.export_bg_var
        ).pack(anchor="w")

        ttk.Checkbutton(
            settings_frame,
            text="Generate Playlist",
            variable=self.playlist_var
        ).pack(anchor="w")

        ttk.Checkbutton(
            settings_frame,
            text="Refresh Database",
            variable=self.refresh_db_var
        ).pack(anchor="w")

        # =================================================
        # LIMIT
        # =================================================

        limit_frame = ttk.LabelFrame(
            main,
            text="Limit",
            padding=16
        )

        limit_frame.pack(fill="x", pady=(0, 16))

        self.limit_all_var = tk.BooleanVar(
            value=self.config["LIMIT_ALL"]
        )

        self.limit_var = tk.StringVar(
            value=str(self.config["LIMIT"])
        )

        ttk.Checkbutton(
            limit_frame,
            text="Export All Songs",
            variable=self.limit_all_var,
            command=self.toggle_limit
        ).grid(row=0, column=0, sticky="w")

        ttk.Label(
            limit_frame,
            text="Song Limit"
        ).grid(row=1, column=0, sticky="w", pady=(12, 0))

        self.limit_entry = ttk.Entry(
            limit_frame,
            textvariable=self.limit_var,
            width=15
        )

        self.limit_entry.grid(
            row=2,
            column=0,
            sticky="w",
            pady=(4, 0)
        )

        # =================================================
        # PERFORMANCE
        # =================================================

        perf_frame = ttk.LabelFrame(
            main,
            text="Performance",
            padding=16
        )

        perf_frame.pack(fill="x", pady=(0, 16))

        self.max_workers_var = tk.StringVar(
            value=str(self.config["MAX_WORKERS"])
        )

        ttk.Label(
            perf_frame,
            text="Max Workers"
        ).grid(row=0, column=0, sticky="w")

        ttk.Entry(
            perf_frame,
            textvariable=self.max_workers_var,
            width=15
        ).grid(row=1, column=0, sticky="w", pady=(4, 0))

        # =================================================
        # FOOTER
        # =================================================

        footer = ttk.Frame(main)
        footer.pack(fill="x", pady=(16, 0))

        ttk.Button(
            footer,
            text="Save Config",
            command=self.save_config
        ).pack(side="right")

        self.toggle_limit()

    # =====================================================
    # ACTIONS
    # =====================================================

    def toggle_limit(self):

        if self.limit_all_var.get():
            self.limit_entry.configure(state="disabled")
        else:
            self.limit_entry.configure(state="normal")

    def pick_osu_folder(self):

        path = filedialog.askdirectory()

        if path:
            self.osu_folder_var.set(path)

    def pick_export_folder(self):

        path = filedialog.askdirectory()

        if path:
            self.export_folder_var.set(path)


if __name__ == "__main__":

    root = tk.Tk()

    app = ConfigUI(root)

    root.mainloop()