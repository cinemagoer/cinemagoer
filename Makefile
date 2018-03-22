.PHONY: help clean clean-build clean-pyc clean-docs lint test test-all coverage docs dist

help:
	@echo "clean - clean everything"
	@echo "clean-build - remove build artifacts"
	@echo "clean-pyc - remove Python file artifacts"
	@echo "clean-docs - remove Sphinx documentation artifacts"
	@echo "lint - check style with flake8"
	@echo "test - run tests quickly with the default Python"
	@echo "test-all - run tests on every Python version with tox"
	@echo "coverage - check code coverage quickly with the default Python"
	@echo "docs - generate Sphinx HTML documentation, including API docs"
	@echo "dist - package"

clean: clean-build clean-pyc clean-docs

clean-build:
	rm -fr build/
	rm -fr dist/
	rm -fr *.egg-info

clean-pyc:
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '*~' -exec rm -f {} +

clean-docs:
	make -C docs clean

lint:
	python setup.py flake8

test:
	py.test

test-all:
	tox

coverage:
	py.test --cov-report term-missing --cov=imdb tests

docs:
	$(MAKE) -C docs clean
	$(MAKE) -C docs html

dist: clean
	python setup.py sdist
	python setup.py bdist_wheel
