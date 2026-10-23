PYTHON := .venv/bin/python

.PHONY: setup download test bench smoke
setup:
	uv venv --python 3.12
	uv pip sync --python $(PYTHON) requirements.lock

download:
	$(PYTHON) prepare_model.py

test:
	$(PYTHON) -m unittest discover -s tests -v

bench:
	$(PYTHON) bench.py run

smoke:
	$(PYTHON) bench.py run --variants variants/baseline.json --rounds 1 --tokens 16

.PHONY: bench-cache
bench-cache:
	$(PYTHON) bench.py run --variants variants/baseline.json variants/stream-lru-8.json variants/stream-lru-32.json variants/stream-lfu-32.json variants/stream-lru-64.json variants/stream-packed-64.json --rounds 3 --tokens 64

ROUNDS ?= 3
TOKENS ?= 128

.PHONY: prepare-layout bench-resident bench-streaming bench-matrix
prepare-layout:
	$(PYTHON) prepare_expert_layout.py

bench-resident:
	$(PYTHON) bench.py run --variants variants/baseline.json variants/resident/*.json --rounds $(ROUNDS) --tokens $(TOKENS)

bench-streaming: prepare-layout
	$(PYTHON) bench.py run --variants variants/baseline.json variants/stream-lru-32.json variants/streaming/*.json --rounds $(ROUNDS) --tokens $(TOKENS)

bench-matrix:
	$(MAKE) bench-resident ROUNDS=$(ROUNDS) TOKENS=$(TOKENS)
	$(MAKE) bench-streaming ROUNDS=$(ROUNDS) TOKENS=$(TOKENS)

# GLM on the user's Colibri install (see docs/11-glm-on-this-mac.md)
.PHONY: glm-bench glm-quiet-check glm-quiet glm-quiet-full glm-planned glm-prep-mtp glm-prep-iq2m glm-prep-iq3xxs glm-prep-flash
glm-bench:
	$(PYTHON) glm_bench.py run --name $(or $(NAME),v1)

glm-quiet-check:
	$(PYTHON) glm_quiet.py check

glm-quiet:
	$(PYTHON) glm_quiet.py run --ram-sweep

glm-quiet-full:
	$(PYTHON) glm_quiet.py run --ram-sweep --full

glm-planned:
	$(PYTHON) glm_lab.py planned

# Downloads: run only when you want these experiments (see experiments/glm-experiments.json)
glm-prep-mtp:
	sh scripts/prep_mtp_head.sh

glm-prep-iq2m:
	sh scripts/prep_gguf.sh unsloth/GLM-5.3-GGUF UD-IQ2_M glm-5.3-iq2m

glm-prep-iq3xxs:
	sh scripts/prep_gguf.sh unsloth/GLM-5.3-GGUF UD-IQ3_XXS glm-5.3-iq3xxs

glm-prep-flash:
	sh scripts/prep_gguf.sh unsloth/GLM-5.3-Flash-GGUF UD-IQ3_XXS glm-5.3-flash-iq3xxs

# Lab control app (read-only, local): http://127.0.0.1:8766
.PHONY: lab-app
lab-app:
	$(PYTHON) lab_app/server.py

.PHONY: lab-app-install lab-app-uninstall
lab-app-install:
	sh scripts/lab_app_service.sh install

lab-app-uninstall:
	sh scripts/lab_app_service.sh uninstall

# Small-model plan (docs/13-small-models.md): Qwen3.6-35B-A3B in Colibri format (~23 GB)
.PHONY: glm-prep-qwen36
glm-prep-qwen36:
	df -h ~ | tail -1
	hf download Kreuzzelg/qwen36-35b-a3b-colibri-i4-gs64 --local-dir ~/colibri-models/qwen36-35b-a3b

# Usage: make bench-parallel MODEL=gpt-oss:20b
.PHONY: bench-parallel
bench-parallel:
	$(PYTHON) parallel_bench.py --model $(MODEL)
