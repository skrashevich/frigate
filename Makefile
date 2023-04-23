default_target: local

COMMIT_HASH := $(shell git log -1 --pretty=format:"%h"|tail -1)
VERSION ?= 0.13.0
IMAGE_REPO ?= ghcr.io/blakeblackshear/frigate
CURRENT_UID := $(shell id -u)
CURRENT_GID := $(shell id -g)

version:
	echo 'VERSION = "$(VERSION)-$(COMMIT_HASH)"' > frigate/version.py

local: version
	docker buildx build --target=frigate --tag frigate:latest --load .

local-trt: version
	docker buildx build --target=frigate-tensorrt --tag frigate:latest-tensorrt --load .

amd64: version
	docker buildx build --push --platform linux/amd64 --target=frigate --cache-to type=registry,ref=$(IMAGE_REPO):buildcache --cache-from type=registry,ref=$(IMAGE_REPO):buildcache --tag $(IMAGE_REPO):$(VERSION)-$(COMMIT_HASH) --tag $(IMAGE_REPO):$(VERSION) .
	docker buildx build --push --platform linux/amd64 --target=frigate-tensorrt --cache-to type=registry,ref=$(IMAGE_REPO):buildcache --cache-from type=registry,ref=$(IMAGE_REPO):buildcache --tag $(IMAGE_REPO):$(VERSION)-$(COMMIT_HASH)-tensorrt --tag $(IMAGE_REPO):$(VERSION)-tensorrt .

arm64:
	docker buildx build --platform linux/arm64 --target=frigate --tag $(IMAGE_REPO):$(VERSION)-$(COMMIT_HASH) .

build: version amd64 arm64
	docker buildx build --platform linux/arm64/v8,linux/amd64 --target=frigate --tag $(IMAGE_REPO):$(VERSION)-$(COMMIT_HASH) .

push: build
	docker buildx build --push --platform linux/arm64/v8,linux/amd64 --target=frigate --tag $(IMAGE_REPO):${GITHUB_REF_NAME}-$(COMMIT_HASH) .
	docker buildx build --push --platform linux/amd64 --target=frigate-tensorrt --tag $(IMAGE_REPO):${GITHUB_REF_NAME}-$(COMMIT_HASH)-tensorrt .

run: local
	docker run --rm --publish=5000:5000 --volume=${PWD}/config:/config frigate:latest

run_tests: local
	docker run --rm --workdir=/opt/frigate --entrypoint= frigate:latest python3 -u -m unittest
	docker run --rm --workdir=/opt/frigate --entrypoint= frigate:latest python3 -u -m mypy --config-file frigate/mypy.ini frigate

.PHONY: run_tests
