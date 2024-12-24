SHELL := /bin/bash

.PHONY: format fmt
format fmt: ### Reformat source files and run linters
ifdef CI_LINT_RUN
	pre-commit run --all-files --show-diff-on-failure
else
	pre-commit run --all-files
endif


.PHONY: lint
lint: fmt ### Reformat files, run linters and mypy checks
	mypy src --show-error-codes
