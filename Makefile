PYTHON ?= python
PIP ?= pip

.PHONY: install run test deploy

install:
	$(PYTHON) -m venv .venv
	. .venv/bin/activate || . .venv/Scripts/activate; \
	$(PIP) install --upgrade pip; \
	$(PIP) install -r requirements.txt

run:
	$(PYTHON) main.py run-dev

test:
	$(PYTHON) -m pytest

deploy:
	bash scripts/deploy.sh
