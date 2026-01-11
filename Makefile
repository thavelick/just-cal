# Sane defaults
SHELL := /bin/bash
.ONESHELL:
.SHELLFLAGS := -eu -o pipefail -c
.DELETE_ON_ERROR:
MAKEFLAGS += --warn-undefined-variables
MAKEFLAGS += --no-builtin-rules

# ---------------------- COMMANDS ---------------------------

setup: # Setup project
	@echo "Installing dependencies.."
	uv sync
	@echo "Done."

update: # Update dependencies
	@echo "Updating dependencies.."
	uv sync -U

format: # Format code with ruff
	@echo "Running ruff formatter.."
	uv run ruff format src/ tests/

lint: # Run linters (ruff, pyright)
	@echo "Running ruff linter.."
	uv run ruff check src/ tests/
	@echo "Running pyright type checker.."
	uv run pyright src/ tests/

lint-fix: # Run linters with auto-fix
	@echo "Running ruff formatter and linter with auto-fix.."
	uv run ruff check --fix src/ tests/
	uv run ruff format src/ tests/
	@echo "Running pyright type checker.."
	uv run pyright src/ tests/

test: # Run all tests
	@echo "Running all tests.."
	uv run pytest -q tests/

test-unit: # Run unit tests
	@echo "Running unit tests.."
	uv run pytest tests/

test-coverage: # Run tests with coverage
	@echo "Running tests with coverage.."
	uv run pytest --cov=just_cal --cov-report=html --cov-report=term tests/

test-dist: # Run tests distributed across CPUs
	@echo "Running distributed tests.."
	uv run pytest -n auto tests/

clean: # Clean build artifacts and cache
	@echo "Cleaning build artifacts.."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "htmlcov" -exec rm -rf {} + 2>/dev/null || true
	@echo "Done."

add-dev-dependency: # Add development dependency (usage: make add-dev-dependency DEP=package-name)
	@echo "Adding development dependency: $(DEP)"
	uv add --dev $(DEP)

# -----------------------------------------------------------
# CAUTION: If you have a file with the same name as make
# command, you need to add it to .PHONY below, otherwise it
# won't work. E.g. `make run` wouldn't work if you have
# `run` file in pwd.
.PHONY: help setup update format lint lint-fix test test-unit test-coverage test-dist clean add-dev-dependency

# -----------------------------------------------------------
# -----       (Makefile helpers and decoration)      --------
# -----------------------------------------------------------

.DEFAULT_GOAL := help
# check https://stackoverflow.com/questions/4842424/list-of-ansi-color-escape-sequences
NC = \033[0m
ERR = \033[31;1m
TAB := '%-20s' # Increase if you have long commands

# tput colors
red := $(shell tput setaf 1)
green := $(shell tput setaf 2)
yellow := $(shell tput setaf 3)
blue := $(shell tput setaf 4)
cyan := $(shell tput setaf 6)
cyan80 := $(shell tput setaf 86)
grey500 := $(shell tput setaf 244)
grey300 := $(shell tput setaf 240)
bold := $(shell tput bold)
underline := $(shell tput smul)
reset := $(shell tput sgr0)

help:
	@printf '\n'
	@printf '    $(underline)Available make commands:$(reset)\n\n'
	@# Print commands with comments
	@grep -E '^([a-zA-Z0-9_-]+\.?)+:.+#.+$$' $(MAKEFILE_LIST) \
		| grep -v '^env-' \
		| grep -v '^arg-' \
		| sed 's/:.*#/: #/g' \
		| awk 'BEGIN {FS = "[: ]+#[ ]+"}; \
		{printf "    make $(bold)$(TAB)$(reset) # %s\n", \
			$$1, $$2}'
	@grep -E '^([a-zA-Z0-9_-]+\.?)+:( +\w+-\w+)*$$' $(MAKEFILE_LIST) \
		| grep -v help \
		| awk 'BEGIN {FS = ":"}; \
		{printf "    make $(bold)$(TAB)$(reset)\n", \
			$$1}' || true
	@echo -e ""
