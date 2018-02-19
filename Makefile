.PHONY: clean docs build
PYTHON := python3
build: venv
	venv/bin/python setup.py sdist

wheel: venv
	venv/bin/python && python setup.py bdist_wheel

venv:
	$(PYTHON) -m venv venv
	venv/bin/pip install -r requirements.txt
	venv/bin/pip install -r requirements-dev.txt

clean:
	venv/bin/python setup.py clean
	@cd docs && $(MAKE) clean

	@echo "removing '.tox'"
	@rm -rf .tox

	@echo "removing '.eggs'"
	@rm -rf .eggs

	@echo "removing 'packager.egg-info'"
	@rm -rf packager.egg-info


docs: venv
	@echo building docs
	@source venv/bin/activate && cd docs && $(MAKE) html
