PYTHON ?= python3
VENV_DIR ?= .venv
APP_NAME ?= emulator-files-sync
SRC_FILE ?= app.py
DIST_DIR ?= dist

ifeq ($(OS),Windows_NT)
	VENV_PY := $(VENV_DIR)/Scripts/python.exe
	VENV_PIP := $(VENV_DIR)/Scripts/pip.exe
	PYINSTALLER := $(VENV_DIR)/Scripts/pyinstaller.exe
	EXE_SUFFIX := .exe
else
	VENV_PY := $(VENV_DIR)/bin/python
	VENV_PIP := $(VENV_DIR)/bin/pip
	PYINSTALLER := $(VENV_DIR)/bin/pyinstaller
	EXE_SUFFIX :=
endif

.PHONY: configure venv install run build clean

configure:
	$(PYTHON) scripts/configure.py

venv:
	$(PYTHON) -m venv $(VENV_DIR)

install: configure venv
	$(VENV_PIP) install --upgrade pip
	$(VENV_PIP) install -r requirements.txt

run: install
	$(VENV_PY) $(SRC_FILE)

build: install
	$(PYINSTALLER) --noconfirm --onefile --name $(APP_NAME) $(SRC_FILE)
	@echo "Build complete: $(DIST_DIR)/$(APP_NAME)$(EXE_SUFFIX)"

clean:
	rm -rf build $(DIST_DIR) __pycache__ *.spec $(VENV_DIR)
