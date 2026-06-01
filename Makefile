PYTHON ?= python3
VENV_DIR ?= .venv
APP_NAME ?= Emulator Files Sync
SRC_FILE ?= app.py
DIST_DIR ?= dist

ifeq ($(OS),Windows_NT)
	VENV_PY := $(VENV_DIR)\Scripts\python.exe
	VENV_PIP := $(VENV_DIR)\Scripts\pip.exe
	PYINSTALLER := $(VENV_DIR)\Scripts\pyinstaller.exe
	EXE_SUFFIX := .exe
	DATA_SEP := ;
	PYTHON ?= python
	ICON_FILE := images\EFS.ico
else
	VENV_PY := $(VENV_DIR)/bin/python
	VENV_PIP := $(VENV_DIR)/bin/pip
	PYINSTALLER := $(VENV_DIR)/bin/pyinstaller
	EXE_SUFFIX :=
	DATA_SEP := :
	ICON_FILE := images/EFS.ico
endif

PYINSTALLER_DATA_ARGS := --add-data "mappings$(DATA_SEP)mappings" --add-data "images$(DATA_SEP)images"

.PHONY: configure venv install run build clean

all: build

configure:
	$(PYTHON) scripts/configure.py

venv:
	$(PYTHON) -m venv $(VENV_DIR)

install: configure venv
	$(VENV_PY) -m pip install --upgrade pip
	$(VENV_PIP) install --upgrade pip
	$(VENV_PIP) install -r requirements.txt

run: install
	$(VENV_PY) $(SRC_FILE)

build: install
	$(PYINSTALLER) --noconfirm --onefile --name "$(APP_NAME)" --icon "$(ICON_FILE)" --hidden-import PIL._tkinter_finder $(PYINSTALLER_DATA_ARGS) $(SRC_FILE)
	@echo "Build complete: $(DIST_DIR)/$(APP_NAME)$(EXE_SUFFIX)"

clean:
ifeq ($(OS),Windows_NT)
	-rmdir /s /q build 2>nul
	-rmdir /s /q $(DIST_DIR) 2>nul
	-rmdir /s /q __pycache__ 2>nul
	-del /f /q *.spec 2>nul
	-rmdir /s /q $(VENV_DIR) 2>nul
else
	rm -rf build $(DIST_DIR) __pycache__ *.spec $(VENV_DIR)
endif
