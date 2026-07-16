PYTHON ?= python

.PHONY: download run test validate clean

download:
	$(PYTHON) scripts/download_data.py

run:
	$(PYTHON) scripts/run_pipeline.py

test:
	$(PYTHON) -m pytest

validate:
	$(PYTHON) scripts/validate_outputs.py

clean:
	$(PYTHON) scripts/clean_outputs.py
