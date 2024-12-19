.PHONY: all test clean
all test clean:

SHELL := /bin/sh -e

venv:
	python -m venv venv
	. venv/bin/activate; \
	pip install -U pip pip-tools

.PHONY: requirements.txt
requirements.txt: requirements.in venv
	. venv/bin/activate; \
	python -m piptools compile requirements.in --output-file $@ --verbose

requirements-dev.txt: requirements-dev.in requirements.txt
	. venv/bin/activate; \
	python -m piptools compile requirements.in requirements-dev.in --output-file $@ --verbose

.PHONY: install
install: requirements-dev.txt
	. venv/bin/activate; \
	python -m piptools sync $?; \
	pre-commit install


.PHONY: format fmt
format fmt: ### Reformat source files and run linters
ifdef CI_LINT_RUN
	. venv/bin/activate; \
	pre-commit run --all-files --show-diff-on-failure
else
	. venv/bin/activate; \
	pre-commit run --all-files
endif

.PHONY: lint
lint: format
	. venv/bin/activate; \
	mypy src
