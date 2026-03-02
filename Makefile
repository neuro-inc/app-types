# checkmake: ignore=phony
IMAGE_REPO ?= ghcr.io/neuro-inc
IMAGE_NAME ?= post-deployment-app-hook
IMAGE_TAG ?= latest
PYTHON_VERSION ?= $(strip $(shell cat .python-version 2>/dev/null || echo 3.12))
POETRY_VERSION ?= $(strip $(shell cat .poetry-version 2>/dev/null || echo 2.2.1))
IMAGE_REF = $(IMAGE_REPO)/$(IMAGE_NAME):$(IMAGE_TAG)

.PHONY: format fmt
format fmt: ### Reformat source files and run linters
ifdef CI_LINT_RUN
	poetry run pre-commit run --all-files --show-diff-on-failure
else
	poetry run pre-commit run --all-files
endif

.PHONY: lock
lock:
	poetry lock

.PHONY: setup
setup:
	poetry install -E fixtures --with dev
	poetry run pre-commit install;

.PHONY: lint
lint: fmt ### Reformat files, run linters and mypy checks
	poetry run mypy src --show-error-codes

.PHONY: build-hook-image
build-hook-image:
	docker build \
		--build-arg PYTHON_VERSION=$(PYTHON_VERSION) \
		--build-arg POETRY_VERSION=$(POETRY_VERSION) \
		-t $(IMAGE_NAME):latest \
		.;

.PHONY: push-hook-image
push-hook-image:
	docker tag $(IMAGE_NAME):latest $(IMAGE_REF)
	docker push $(IMAGE_REF)

.PHONY: test-unit
test-unit:
	poetry run pytest -vv tests/unit --disable-pytest-warnings

.PHONY: dist
dist:
	poetry build --clean

.PHONY: print-schema
print-schema:
	@poetry run python -c 'import json; from apolo_app_types import $(type_name); print(json.dumps($(type_name).model_json_schema()))'
