# emulator-files-sync

A Python desktop app that syncs ROM files between emulator directory layouts using CSV mappings.

## Features

- CustomTkinter GUI with:
  - Source and destination profile dropdowns
  - Source and destination root folder pickers
  - Status box with neutral, error, and success messages
  - Systems table showing common `System` entries between selected CSV profiles
  - Per-system checkboxes plus **Select All** and **Select None** controls directly above the table
- Recursive copy of selected systems from source mapping directories to destination mapping directories
- Progress bar with percent complete and current system label
- Completion summary with copied system and file totals

## Mapping files

Profile CSV files are loaded from `/tmp/workspace/KertDawg/emulator-files-sync/mappings` and must include:

```csv
System,Directory
```

The app intersects `System` names from source and destination profiles and builds copy rows from matching entries.

## Run locally

```bash
cd /tmp/workspace/KertDawg/emulator-files-sync
make run
```

## Build single-file executable

```bash
cd /tmp/workspace/KertDawg/emulator-files-sync
make build
```

The `Makefile` creates a Python virtual environment, installs dependencies, and runs PyInstaller with OS-aware executable naming.
