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
