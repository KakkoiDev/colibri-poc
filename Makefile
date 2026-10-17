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
