# checkmake: ignore=phony
IMAGE_REPO ?= ghcr.io/neuro-inc
IMAGE_NAME ?= post-deployment-app-hook
IMAGE_TAG ?= latest
IMAGE_REF = $(IMAGE_REPO)/$(IMAGE_NAME):$(IMAGE_TAG)

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

.PHONY: build-hook-image
build-hook-image:
	docker build \
		-t $(IMAGE_NAME):latest \
		.;

.PHONY: push-hook-image
push-hook-image:
	docker tag $(IMAGE_NAME):latest $(IMAGE_REF)
	docker push $(IMAGE_REF)

.PHONY: test-unit
test-unit:
	pytest -vv tests/unit
