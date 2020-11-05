# This file is part of ranger, the console file manager.
# License: GNU GPL version 3, see the file "AUTHORS" for details.

NAME = ranger
VERSION = $(shell grep -m 1 -o '[0-9][0-9.]\+\S*' README.md)
NAME_RIFLE = rifle
VERSION_RIFLE = $(VERSION)
SNAPSHOT_NAME ?= $(NAME)-$(VERSION)-$(shell git rev-parse HEAD | cut -b 1-8).tar.gz
# Find suitable python version (need python >= 2.6 or 3.1):
PYTHON ?= $(shell \
	     (which python3) \
	     || (python -c 'import sys; sys.exit(sys.version < "2.6")' && \
	      which python) \
	     || (python2 -c 'import sys; sys.exit(sys.version < "2.6")' && \
	         which python2) \
	   )
ifeq ($(PYTHON),)
  $(error No suitable python found.)
endif
SETUPOPTS ?= '--record=install_log.txt'
DOCDIR ?= doc/pydoc
DESTDIR ?= /
PREFIX ?= /usr/local
PYOPTIMIZE ?= 1
FILTER ?= .

CWD = $(shell pwd)

default: test compile
	@echo 'Run `make options` for a list of all options'

options: help
	@echo
	@echo 'Options:'
	@echo 'PYTHON = $(PYTHON)'
	@echo 'PYOPTIMIZE = $(PYOPTIMIZE)'
	@echo 'DOCDIR = $(DOCDIR)'
	@echo 'DESTDIR = $(DESTDIR)'

help:
	@echo 'make:                 Test and compile ranger.'
	@echo 'make install:         Install $(NAME)'
	@echo 'make pypi_sdist:      Release a new sdist to PyPI'
	@echo 'make clean:           Remove the compiled files (*.pyc, *.pyo)'
	@echo 'make doc:             Create the pydoc documentation'
	@echo 'make cleandoc:        Remove the pydoc documentation'
	@echo 'make man:             Compile the manpage with "pod2man"'
	@echo 'make manhtml:         Compile the html manpage with "pod2html"'
	@echo 'make snapshot:        Create a tar.gz of the current git revision'
	@echo 'make test:            Test everything'
	@echo 'make test_pylint:     Test using pylint'
	@echo 'make test_flake8:     Test using flake8'
	@echo 'make test_doctest:    Test using doctest'
	@echo 'make test_pytest:     Test using pytest'
	@echo 'make test_other:      Verify the manpage is complete'
	@echo 'make test_py:         Run all python tests, including manpage completeness'
	@echo 'make test_shellcheck: Test using shellcheck'
	@echo 'make todo:            Look for TODO and XXX markers in the source code'

install:
	$(PYTHON) setup.py install $(SETUPOPTS) \
		'--prefix=$(PREFIX)' '--root=$(DESTDIR)' \
		--optimize=$(PYOPTIMIZE)

compile: clean
	PYTHONOPTIMIZE=$(PYOPTIMIZE) $(PYTHON) -m compileall -q ranger

clean:
	find ranger -regex .\*\.py[co]\$$ -delete
	find ranger -depth -name __pycache__ -type d -exec rm -r -- {} \;

doc: cleandoc
	mkdir -p $(DOCDIR)
	cd $(DOCDIR); \
		$(PYTHON) -c 'import pydoc, sys; \
		sys.path[0] = "$(CWD)"; \
		pydoc.writedocs("$(CWD)")'
	find . -name \*.html -exec sed -i 's|'"$(CWD)"'|../..|g' -- {} \;

TEST_PATHS_MAIN = \
	$(shell find ./ranger -mindepth 1 -maxdepth 1 -type d \
		! -name '__pycache__' \
		! -path './ranger/config' \
		! -path './ranger/data' \
	) \
	./ranger/__init__.py \
	$(shell find ./doc/tools ./examples -type f -name '*.py') \
	./ranger.py \
	./setup.py \
	./tests
TEST_PATH_CONFIG = ./ranger/config

test_pylint:
	@echo "Running pylint..."
	pylint $(TEST_PATHS_MAIN)
	pylint --rcfile=$(TEST_PATH_CONFIG)/.pylintrc $(TEST_PATH_CONFIG)

test_flake8:
	@echo "Running flake8..."
	flake8 $(TEST_PATHS_MAIN) $(TEST_PATH_CONFIG)

test_doctest:
	@echo "Running doctests..."
	@set -e; \
	for FILE in $(shell grep -IHm 1 doctest -r ranger | grep $(FILTER) | cut -d: -f1); do \
		echo "Testing $$FILE..."; \
		RANGER_DOCTEST=1 PYTHONPATH=".:"$$PYTHONPATH ${PYTHON} $$FILE; \
	done

test_pytest:
	@echo "Running py.test tests..."
	py.test tests

test_py: test_pylint test_flake8 test_doctest test_pytest test_other
	@echo "Finished python and documentation tests!"

test_shellcheck:
	@echo "Running shellcheck..."
	sed '2,$$s/^\(\s*\)#/\1/' ./ranger/data/scope.sh | shellcheck -a -

test_other:
	@echo "Checking completeness of man page..."
	@tests/manpage_completion_test.py

test: test_py test_shellcheck
	@echo "Finished testing: All tests passed!"

doc/ranger.1: doc/ranger.pod README.md
	pod2man --stderr --center='ranger manual' \
		--date='$(NAME)-$(VERSION)' \
		--release=$(shell date -u '+%Y-%m-%d') \
		doc/ranger.pod doc/ranger.1

doc/rifle.1: doc/rifle.pod README.md
	pod2man --stderr --center='rifle manual' \
		--date='$(NAME_RIFLE)-$(VERSION_RIFLE)' \
		--release=$(shell date -u '+%Y-%m-%d') \
		doc/rifle.pod doc/rifle.1

man: doc/ranger.1 doc/rifle.1

manhtml:
	pod2html doc/ranger.pod --outfile=doc/ranger.1.html

cleandoc:
	test -d $(DOCDIR) && rm -- $(DOCDIR)/*.html || true

snapshot:
	git archive --prefix='$(NAME)-$(VERSION)/' --format=tar HEAD | gzip > $(SNAPSHOT_NAME)

dist: snapshot

todo:
	@grep --color -Ion '\(TODO\|XXX\).*' -r ranger

.PHONY: clean cleandoc compile default dist doc help install man manhtml \
	options snapshot test test_pylint test_flake8 test_doctest test_pytest \
	test_other todo pypi_sdist
