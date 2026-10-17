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
