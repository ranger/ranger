# This file is part of ranger, the console file manager.
# License: GNU GPL version 3, see the file "AUTHORS" for details.

NAME = ranger
VERSION = $(shell grep -m 1 -o '[0-9][0-9.]\+' README.md)
NAME_RIFLE = rifle
VERSION_RIFLE = $(VERSION)
SNAPSHOT_NAME ?= $(NAME)-$(VERSION)-$(shell git rev-parse HEAD | cut -b 1-8).tar.gz
# Find suitable python version (need python >= 2.6 or 3.1):
PYTHON ?= $(shell python -c 'import sys; sys.exit(sys.version < "2.6")' && \
	which python || which python3.3 || which python3.2 || which python3.1 || \
	which python3 || which python2.7 || which python2.6)
SETUPOPTS ?= '--record=install_log.txt'
DOCDIR ?= doc/pydoc
DESTDIR ?= /
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
	@echo 'make:          Test and compile ranger.'
	@echo 'make install:  Install $(NAME)'
	@echo 'make clean:    Remove the compiled files (*.pyc, *.pyo)'
	@echo 'make doc:      Create the pydoc documentation'
	@echo 'make cleandoc: Remove the pydoc documentation'
	@echo 'make man:      Compile the manpage with "pod2man"'
	@echo 'make manhtml:  Compile the html manpage with "pod2html"'
	@echo 'make snapshot: Create a tar.gz of the current git revision'
	@echo 'make test:     Test all testable modules of ranger'
	@echo 'make todo:     Look for TODO and XXX markers in the source code'

install:
	$(PYTHON) setup.py install $(SETUPOPTS) \
		'--root=$(DESTDIR)' --optimize=$(PYOPTIMIZE)

compile: clean
	PYTHONOPTIMIZE=$(PYOPTIMIZE) $(PYTHON) -m compileall -q ranger

clean:
	find ranger -regex .\*\.py[co]\$$ -delete
	find ranger -depth -name __pycache__ -type d -exec rm -rf -- {} \;

doc: cleandoc
	mkdir -p $(DOCDIR)
	cd $(DOCDIR); \
		$(PYTHON) -c 'import pydoc, sys; \
		sys.path[0] = "$(CWD)"; \
		pydoc.writedocs("$(CWD)")'
	find . -name \*.html -exec sed -i 's|'"$(CWD)"'|../..|g' -- {} \;

TEST_PATHS_MAIN = \
	$(shell find ranger -mindepth 1 -maxdepth 1 -type d -and -not -name '__pycache__' -and -not -path 'ranger/config' -and -not -path 'ranger/data') \
	ranger/__init__.py \
	$(shell find . '(' -path './ranger' -or -path './tests' ')' -prune -or -type f -name '*.py' -print) \
	tests
TEST_PATH_CONFIG = ranger/config

test:
	@echo "Running pylint..."
	pylint $(TEST_PATHS_MAIN)
	pylint --rcfile=$(TEST_PATH_CONFIG)/pylintrc $(TEST_PATH_CONFIG)
	@echo "Running flake8..."
	flake8 $(TEST_PATHS_MAIN) $(TEST_PATH_CONFIG)
	@echo "Running doctests..."
	@for FILE in $(shell grep -IHm 1 doctest -r ranger | grep $(FILTER) | cut -d: -f1); do \
		echo "Testing $$FILE..."; \
		RANGER_DOCTEST=1 PYTHONPATH=".:"$$PYTHONPATH ${PYTHON} $$FILE; \
	done
	@if type py.test > /dev/null; then \
		echo "Running py.test tests..."; \
		py.test tests; \
	else \
		echo "WARNING: Couldn't run some tests because py.test is not installed!"; \
	fi
	@echo "Finished testing."

man:
	pod2man --stderr --center='ranger manual' --date='$(NAME)-$(VERSION)' \
		--release=$(shell date +%x) doc/ranger.pod doc/ranger.1
	pod2man --stderr --center='rifle manual' --date='$(NAME_RIFLE)-$(VERSION_RIFLE)' \
		--release=$(shell date +%x) doc/rifle.pod doc/rifle.1

manhtml:
	pod2html doc/ranger.pod --outfile=doc/ranger.1.html

cleandoc:
	test -d $(DOCDIR) && rm -f -- $(DOCDIR)/*.html || true

snapshot:
	git archive --prefix='$(NAME)-$(VERSION)/' --format=tar HEAD | gzip > $(SNAPSHOT_NAME)

dist: snapshot

todo:
	@grep --color -Ion '\(TODO\|XXX\).*' -r ranger

.PHONY: clean cleandoc compile default dist doc help install man manhtml options snapshot test todo
