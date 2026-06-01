from __future__ import annotations

import csv
import os
import queue
import shutil
import threading
from dataclasses import dataclass
from pathlib import Path
from tkinter import filedialog
from typing import Dict, List

import customtkinter as ctk


ctk.set_appearance_mode("system")
ctk.set_default_color_theme("blue")

APP_TITLE = "Emulator Files Sync"
MAPPINGS_DIR = Path(__file__).resolve().parent / "mappings"


@dataclass
class SystemRow:
    system: str
    src_dir: str
    dst_dir: str


class App(ctk.CTk):
    def __init__(self) -> None:
        super().__init__()
        self.title(APP_TITLE)
        self.geometry("1180x760")
        self.minsize(960, 620)

        self.profile_files = self._discover_profile_files()
        self.src_map: Dict[str, str] = {}
        self.dst_map: Dict[str, str] = {}
        self.rows: List[SystemRow] = []
        self.row_vars: Dict[str, ctk.BooleanVar] = {}
        self.ui_queue: queue.Queue = queue.Queue()
        self.sync_thread: threading.Thread | None = None

        self.source_profile_var = ctk.StringVar(value="")
        self.dest_profile_var = ctk.StringVar(value="")
        self.source_root_var = ctk.StringVar(value="")
        self.dest_root_var = ctk.StringVar(value="")

        self._build_layout()
        self._bind_events()
        self._set_status(
            "Select the source and destination systems and the folders for each. Press Sync to start.",
            "neutral",
        )
        self.after(100, self._process_ui_queue)

    def _discover_profile_files(self) -> Dict[str, Path]:
        if not MAPPINGS_DIR.exists():
            return {}
        files = sorted(MAPPINGS_DIR.glob("*.csv"), key=lambda p: p.stem.lower())
        return {path.stem: path for path in files}

    def _build_layout(self) -> None:
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        self.status_frame = ctk.CTkFrame(self, corner_radius=8)
        self.status_frame.grid(row=0, column=0, sticky="ew", padx=16, pady=(16, 8))
        self.status_frame.grid_columnconfigure(0, weight=1)
        self.status_label = ctk.CTkLabel(
            self.status_frame,
            text="",
            justify="left",
            anchor="w",
            wraplength=1060,
            padx=10,
            pady=10,
        )
        self.status_label.grid(row=0, column=0, sticky="ew")

        self.main_frame = ctk.CTkFrame(self, corner_radius=8)
        self.main_frame.grid(row=2, column=0, sticky="nsew", padx=16, pady=(0, 16))
        self.main_frame.grid_columnconfigure(1, weight=1)
        self.main_frame.grid_rowconfigure(0, weight=1)

        self.left_panel = ctk.CTkFrame(self.main_frame, width=320, corner_radius=8)
        self.left_panel.grid(row=0, column=0, sticky="nsw", padx=(0, 10), pady=10)
        self.left_panel.grid_propagate(False)
        self.left_panel.grid_columnconfigure(1, weight=1)

        left_row = 0
        ctk.CTkLabel(self.left_panel, text="Source System", anchor="w").grid(
            row=left_row, column=0, columnspan=2, sticky="ew", padx=12, pady=(12, 4)
        )
        left_row += 1
        profiles = list(self.profile_files.keys())
        self.source_profile_menu = ctk.CTkOptionMenu(
            self.left_panel,
            variable=self.source_profile_var,
            values=profiles if profiles else ["No mappings found"],
        )
        self.source_profile_menu.grid(
            row=left_row, column=0, columnspan=2, sticky="ew", padx=12, pady=(0, 10)
        )
        left_row += 1

        ctk.CTkLabel(self.left_panel, text="Destination System", anchor="w").grid(
            row=left_row, column=0, columnspan=2, sticky="ew", padx=12, pady=(4, 4)
        )
        left_row += 1
        self.dest_profile_menu = ctk.CTkOptionMenu(
            self.left_panel,
            variable=self.dest_profile_var,
            values=profiles if profiles else ["No mappings found"],
        )
        self.dest_profile_menu.grid(
            row=left_row, column=0, columnspan=2, sticky="ew", padx=12, pady=(0, 10)
        )
        left_row += 1

        ctk.CTkLabel(self.left_panel, text="Source Root Folder", anchor="w").grid(
            row=left_row, column=0, columnspan=2, sticky="ew", padx=12, pady=(4, 4)
        )
        left_row += 1
        self.source_entry = ctk.CTkEntry(
            self.left_panel, textvariable=self.source_root_var, placeholder_text="Select source folder"
        )
        self.source_entry.grid(row=left_row, column=0, sticky="ew", padx=(12, 6), pady=(0, 10))
        ctk.CTkButton(self.left_panel, text="Browse", width=90, command=self._choose_source_folder).grid(
            row=left_row, column=1, sticky="ew", padx=(0, 12), pady=(0, 10)
        )
        left_row += 1

        ctk.CTkLabel(self.left_panel, text="Destination Root Folder", anchor="w").grid(
            row=left_row, column=0, columnspan=2, sticky="ew", padx=12, pady=(4, 4)
        )
        left_row += 1
        self.dest_entry = ctk.CTkEntry(
            self.left_panel, textvariable=self.dest_root_var, placeholder_text="Select destination folder"
        )
        self.dest_entry.grid(row=left_row, column=0, sticky="ew", padx=(12, 6), pady=(0, 10))
        ctk.CTkButton(self.left_panel, text="Browse", width=90, command=self._choose_dest_folder).grid(
            row=left_row, column=1, sticky="ew", padx=(0, 12), pady=(0, 10)
        )
        left_row += 1

        self.sync_button = ctk.CTkButton(self.left_panel, text="Sync", command=self._on_sync_clicked)
        self.sync_button.grid(row=left_row, column=0, columnspan=2, sticky="ew", padx=12, pady=(6, 8))
        left_row += 1

        self.progress_bar = ctk.CTkProgressBar(self.left_panel)
        self.progress_bar.set(0)
        self.progress_bar.grid(row=left_row, column=0, columnspan=2, sticky="ew", padx=12, pady=(0, 2))
        left_row += 1
        self.progress_text = ctk.CTkLabel(self.left_panel, text="Progress: 0%")
        self.progress_text.grid(row=left_row, column=0, columnspan=2, sticky="w", padx=12, pady=(0, 2))
        left_row += 1
        self.current_system_label = ctk.CTkLabel(self.left_panel, text="Current system: None")
        self.current_system_label.grid(row=left_row, column=0, columnspan=2, sticky="w", padx=12, pady=(0, 12))

        self.right_panel = ctk.CTkFrame(self.main_frame, corner_radius=8)
        self.right_panel.grid(row=0, column=1, sticky="nsew", padx=(10, 0), pady=10)
        self.right_panel.grid_columnconfigure(0, weight=1)
        self.right_panel.grid_rowconfigure(2, weight=1)

        # Select controls are intentionally above the systems table.
        controls = ctk.CTkFrame(self.right_panel, fg_color="transparent")
        controls.grid(row=0, column=0, sticky="ew", padx=12, pady=(12, 6))
        ctk.CTkButton(controls, text="Select All", width=120, command=self._select_all_rows).pack(
            side="left", padx=(0, 8)
        )
        ctk.CTkButton(controls, text="Select None", width=120, command=self._select_no_rows).pack(side="left")

        headers = ctk.CTkFrame(self.right_panel, fg_color="transparent")
        headers.grid(row=1, column=0, sticky="ew", padx=12, pady=(0, 4))
        headers.grid_columnconfigure(0, weight=0, minsize=110)
        headers.grid_columnconfigure(1, weight=1)
        headers.grid_columnconfigure(2, weight=1)
        ctk.CTkLabel(headers, text="System", anchor="w", font=ctk.CTkFont(weight="bold")).grid(
            row=0, column=0, sticky="ew", padx=(6, 8)
        )
        ctk.CTkLabel(headers, text="Source Directory", anchor="w", font=ctk.CTkFont(weight="bold")).grid(
            row=0, column=1, sticky="ew", padx=8
        )
        ctk.CTkLabel(headers, text="Destination Directory", anchor="w", font=ctk.CTkFont(weight="bold")).grid(
            row=0, column=2, sticky="ew", padx=8
        )

        self.table_frame = ctk.CTkScrollableFrame(self.right_panel)
        self.table_frame.grid(row=2, column=0, sticky="nsew", padx=12, pady=(0, 12))
        self.table_frame.grid_columnconfigure(0, weight=0, minsize=110)
        self.table_frame.grid_columnconfigure(1, weight=1)
        self.table_frame.grid_columnconfigure(2, weight=1)

    def _bind_events(self) -> None:
        self.source_profile_var.trace_add("write", lambda *_: self._on_profile_change())
        self.dest_profile_var.trace_add("write", lambda *_: self._on_profile_change())
        profiles = list(self.profile_files.keys())
        if profiles:
            self.source_profile_var.set(profiles[0])
            self.dest_profile_var.set(profiles[0])

    def _set_status(self, message: str, level: str) -> None:
        palette = {
            "neutral": ("#DBEAFE", "#1E3A8A"),
            "error": ("#FEE2E2", "#991B1B"),
            "success": ("#DCFCE7", "#166534"),
        }
        bg, fg = palette.get(level, palette["neutral"])
        self.status_frame.configure(fg_color=bg)
        self.status_label.configure(text=message, text_color=fg)

    def _choose_source_folder(self) -> None:
        chosen = filedialog.askdirectory()
        if chosen:
            self.source_root_var.set(chosen)

    def _choose_dest_folder(self) -> None:
        chosen = filedialog.askdirectory()
        if chosen:
            self.dest_root_var.set(chosen)

    def _load_mapping(self, profile_name: str) -> Dict[str, str]:
        mapping_path = self.profile_files.get(profile_name)
        if mapping_path is None:
            return {}

        mapping: Dict[str, str] = {}
        with mapping_path.open(newline="", encoding="utf-8") as handle:
            reader = csv.DictReader(handle)
            if "System" not in (reader.fieldnames or []) or "Directory" not in (reader.fieldnames or []):
                raise ValueError(f"{mapping_path.name} must include System and Directory columns.")
            for row in reader:
                system = (row.get("System") or "").strip()
                directory = (row.get("Directory") or "").strip()
                if system and directory:
                    mapping[system] = directory
        return mapping

    def _on_profile_change(self) -> None:
        src_profile = self.source_profile_var.get().strip()
        dst_profile = self.dest_profile_var.get().strip()
        if not src_profile or not dst_profile:
            return
        if src_profile not in self.profile_files or dst_profile not in self.profile_files:
            self.src_map = {}
            self.dst_map = {}
            self._render_rows([])
            return

        try:
            self.src_map = self._load_mapping(src_profile)
            self.dst_map = self._load_mapping(dst_profile)
            common = sorted(set(self.src_map.keys()) & set(self.dst_map.keys()), key=str.lower)
            rows = [SystemRow(system=s, src_dir=self.src_map[s], dst_dir=self.dst_map[s]) for s in common]
            self._render_rows(rows)
            self._set_status(
                "Select the source and destination systems and the folders for each. Press Sync to start.",
                "neutral",
            )
        except Exception as exc:
            self._render_rows([])
            self._set_status(f"Error loading CSV mappings: {exc}", "error")

    def _clear_table(self) -> None:
        for child in self.table_frame.winfo_children():
            child.destroy()

    def _render_rows(self, rows: List[SystemRow]) -> None:
        self.rows = rows
        self.row_vars = {}
        self._clear_table()
        if not rows:
            ctk.CTkLabel(self.table_frame, text="No common systems found for selected profiles.").grid(
                row=0, column=0, columnspan=3, sticky="w", padx=8, pady=8
            )
            return

        for index, row in enumerate(rows):
            row_var = ctk.BooleanVar(value=False)
            self.row_vars[row.system] = row_var
            checkbox = ctk.CTkCheckBox(self.table_frame, text=row.system, variable=row_var)
            checkbox.grid(row=index, column=0, sticky="w", padx=(6, 8), pady=4)

            ctk.CTkLabel(self.table_frame, text=row.src_dir, anchor="w").grid(
                row=index, column=1, sticky="ew", padx=8, pady=4
            )
            ctk.CTkLabel(self.table_frame, text=row.dst_dir, anchor="w").grid(
                row=index, column=2, sticky="ew", padx=8, pady=4
            )

    def _select_all_rows(self) -> None:
        for row_var in self.row_vars.values():
            row_var.set(True)

    def _select_no_rows(self) -> None:
        for row_var in self.row_vars.values():
            row_var.set(False)

    def _selected_rows(self) -> List[SystemRow]:
        selected = []
        for row in self.rows:
            var = self.row_vars.get(row.system)
            if var and var.get():
                selected.append(row)
        return selected

    def _validate_sync_inputs(self) -> str | None:
        if not self.source_profile_var.get().strip() or self.source_profile_var.get() not in self.profile_files:
            return "Please select a source system."
        if not self.dest_profile_var.get().strip() or self.dest_profile_var.get() not in self.profile_files:
            return "Please select a destination system."
        if not self.source_root_var.get().strip():
            return "Please select a source folder."
        if not self.dest_root_var.get().strip():
            return "Please select a destination folder."
        if not self._selected_rows():
            return "Please select at least one system to sync."
        return None

    def _on_sync_clicked(self) -> None:
        validation_error = self._validate_sync_inputs()
        if validation_error:
            self._set_status(validation_error, "error")
            return

        source_root = Path(self.source_root_var.get().strip())
        dest_root = Path(self.dest_root_var.get().strip())
        selected_rows = self._selected_rows()

        self.sync_button.configure(state="disabled")
        self.progress_bar.set(0)
        self.progress_text.configure(text="Progress: 0%")
        self.current_system_label.configure(text="Current system: Preparing...")
        self._set_status("Sync in progress...", "neutral")

        self.sync_thread = threading.Thread(
            target=self._sync_worker,
            args=(source_root, dest_root, selected_rows),
            daemon=True,
        )
        self.sync_thread.start()

    def _sync_worker(self, source_root: Path, dest_root: Path, selected_rows: List[SystemRow]) -> None:
        try:
            total_files = 0
            for row in selected_rows:
                src_dir = source_root / row.src_dir
                for _, _, filenames in os.walk(src_dir):
                    total_files += len(filenames)

            copied = 0
            systems_copied = 0
            for row in selected_rows:
                self.ui_queue.put(("current", row.system))
                src_dir = source_root / row.src_dir
                dst_dir = dest_root / row.dst_dir

                if not src_dir.exists():
                    self.ui_queue.put(("warn", f"Skipped {row.system}: source path does not exist ({src_dir})."))
                    continue

                dst_dir.mkdir(parents=True, exist_ok=True)
                for root, _, filenames in os.walk(src_dir):
                    root_path = Path(root)
                    rel = root_path.relative_to(src_dir)
                    target_root = dst_dir / rel
                    target_root.mkdir(parents=True, exist_ok=True)
                    for file_name in filenames:
                        src_file = root_path / file_name
                        dst_file = target_root / file_name
                        shutil.copy2(src_file, dst_file)
                        copied += 1
                        percent = (copied / total_files) if total_files else 1.0
                        self.ui_queue.put(("progress", percent, copied, total_files))

                systems_copied += 1

            self.ui_queue.put(("done", systems_copied, copied))
        except Exception as exc:
            self.ui_queue.put(("error", str(exc)))

    def _process_ui_queue(self) -> None:
        try:
            while True:
                payload = self.ui_queue.get_nowait()
                event = payload[0]
                if event == "current":
                    self.current_system_label.configure(text=f"Current system: {payload[1]}")
                elif event == "progress":
                    percent, copied, total = payload[1], payload[2], payload[3]
                    self.progress_bar.set(percent)
                    self.progress_text.configure(text=f"Progress: {percent * 100:.1f}% ({copied}/{total})")
                elif event == "warn":
                    self._set_status(payload[1], "error")
                elif event == "error":
                    self._set_status(f"Sync failed: {payload[1]}", "error")
                    self.current_system_label.configure(text="Current system: None")
                    self.sync_button.configure(state="normal")
                elif event == "done":
                    systems, files = payload[1], payload[2]
                    self.progress_bar.set(1)
                    self.progress_text.configure(text="Progress: 100%")
                    self.current_system_label.configure(text="Current system: Complete")
                    self._set_status(f"Sync complete. Copied {systems} systems and {files} total files.", "success")
                    self.sync_button.configure(state="normal")
        except queue.Empty:
            pass
        finally:
            self.after(100, self._process_ui_queue)


def main() -> None:
    app = App()
    app.mainloop()


if __name__ == "__main__":
    main()
