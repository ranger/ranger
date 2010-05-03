NAME = ranger
VERSION = 1.0.4
PYTHON ?= python
DOCDIR ?= doc/pydoc
PREFIX ?= /usr
MANPREFIX ?= /share/man
PYTHONOPTIMIZE ?= 2
CWD = $(shell pwd)
PYTHON_SITE_DEST ?= $(shell $(PYTHON) -c 'import sys; sys.stdout.write( \
	[p for p in sys.path if "site" in p][0])' 2> /dev/null)

default: test compile
	@echo 'Run `make options` for a list of all options'

options: help
	@echo
	@echo 'Options:'
	@echo 'PYTHON = $(PYTHON)'
	@echo 'PYTHONOPTIMIZE = $(PYTHONOPTIMIZE)'
	@echo 'PYTHON_SITE_DEST = $(PYTHON_SITE_DEST)'
	@echo 'PREFIX = $(PREFIX)'
	@echo 'MANPREFIX = $(MANPREFIX)'
	@echo 'DOCDIR = $(DOCDIR)'

help:
	@echo 'make: Compile $(NAME)'
	@echo 'make doc: Create the pydoc documentation'
	@echo 'make install: Install ranger'
	@echo 'make clean: Remove the compiled files (*.pyc, *.pyo)'
	@echo 'make cleandoc: Remove the pydoc documentation'
	@echo 'make uninstall: Uninstall ranger'
	@echo 'make snapshot: Create a tar.gz of the current git revision'
	@echo 'make test: Run all unittests.'

all: test compile install

install:
	@if [ '$(PYTHON_SITE_DEST)' == '' ]; then \
		echo -n 'Cannot find a suitable destination for the files.'; \
		echo '  Please install $(NAME) manually.'; \
		false; \
	fi
	@echo "Installing $(NAME) version $(VERSION)..."
	@mkdir -p $(PREFIX)/bin
	cp -f ranger.py $(PREFIX)/bin/ranger
	@mkdir -p $(PYTHON_SITE_DEST)
	cp -fruT ranger $(PYTHON_SITE_DEST)/ranger
	@chmod 755 $(PREFIX)/bin/ranger
	@chmod -R +rX $(PYTHON_SITE_DEST)/ranger
	@mkdir -p $(PREFIX)$(MANPREFIX)/man1
	cp -f doc/ranger.1 $(PREFIX)$(MANPREFIX)/man1/ranger.1
	@chmod 644 $(PREFIX)$(MANPREFIX)/man1/ranger.1

uninstall:
	rm -f $(PREFIX)/bin/ranger
	rm -f '$(PREFIX)$(MANPREFIX)/man1/ranger.1'
	@if [ '$(PYTHON_SITE_DEST)' == '' ]; then \
		echo 'Cannot find a possible location of rangers library files'; \
		false; \
	fi
	rm -rf '$(PYTHON_SITE_DEST)/ranger/*'
	@echo 'NOTE: By default, configuration files are stored at "~/.ranger".'
	@echo 'This script will not delete those.'

compile: clean
	@echo 'Compiling...'
	python -m compileall -q ranger
	PYTHONOPTIMIZE=$(PYTHONOPTIMIZE) python -m compileall -q ranger

clean:
	find . -regex .\*.py[co]\$$ -exec rm -f -- {} \;

doc: cleandoc
	mkdir -p $(DOCDIR)
	cd $(DOCDIR); \
		$(PYTHON) -c 'import pydoc, sys; \
		sys.path[0] = "$(CWD)"; \
		pydoc.writedocs("$(CWD)")'

cleandoc:
	test -d $(DOCDIR) && rm -f -- $(DOCDIR)/*.html

test:
	./all_tests.py 1
	./all_benchmarks.py 1

snapshot:
	git archive HEAD | gzip > $(NAME)-$(VERSION)-$(shell git rev-parse HEAD | cut -b 1-8).tar.gz

.PHONY: default options all compile clean doc cleandoc test \
	install uninstall snapshot
