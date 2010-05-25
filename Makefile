# Copyright (C) 2009, 2010  Roman Zimbelmann <romanz@lavabit.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

NAME = ranger
VERSION = 1.0.4
PYTHON ?= python
DOCDIR ?= doc/pydoc
PREFIX ?= /usr
MANPREFIX ?= /share/man
PYOPTIMIZE ?= 1
PYTHON_SITE_DEST ?= $(shell $(PYTHON) -c 'import sys; sys.stdout.write( \
	[p for p in sys.path if "site" in p][0])' 2> /dev/null)
BMCOUNT ?= 5  # how often to run the benchmarks?

CWD = $(shell pwd)

default: compile
	@echo 'Run `make options` for a list of all options'

options: help
	@echo
	@echo 'Options:'
	@echo 'PYTHON = $(PYTHON)'
	@echo 'PYOPTIMIZE = $(PYOPTIMIZE)'
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
	@mkdir -p $(DESTDIR)$(PREFIX)/bin
	cp -f ranger.py $(DESTDIR)$(PREFIX)/bin/ranger
	@mkdir -p $(DESTDIR)$(PYTHON_SITE_DEST)
	cp -fruT ranger $(DESTDIR)$(PYTHON_SITE_DEST)/ranger
	@chmod 755 $(DESTDIR)$(PREFIX)/bin/ranger
	@chmod -R +rX $(DESTDIR)$(PYTHON_SITE_DEST)/ranger
	@mkdir -p $(DESTDIR)$(PREFIX)$(MANPREFIX)/man1
	cp -f doc/ranger.1 $(DESTDIR)$(PREFIX)$(MANPREFIX)/man1/ranger.1
	@chmod 644 $(DESTDIR)$(PREFIX)$(MANPREFIX)/man1/ranger.1

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
	PYTHONOPTIMIZE=$(PYOPTIMIZE) $(PYTHON) -m compileall -q ranger

clean:
	@echo 'Cleaning...'
	find . -regex .\*.py[co]\$$ -exec rm -f -- {} \;

doc: cleandoc
	@echo 'Creating pydoc html documentation...'
	mkdir -p $(DOCDIR)
	cd $(DOCDIR); \
		$(PYTHON) -c 'import pydoc, sys; \
		sys.path[0] = "$(CWD)"; \
		pydoc.writedocs("$(CWD)")'

cleandoc:
	@echo 'Removing pydoc html documentation...'
	test -d $(DOCDIR) && rm -f -- $(DOCDIR)/*.html

test:
	@$(PYTHON) all_tests.py 1

bm:
	@$(PYTHON) all_benchmarks.py $(BMCOUNT)

snapshot:
	git archive HEAD | gzip > $(NAME)-$(VERSION)-$(shell git rev-parse HEAD | cut -b 1-8).tar.gz

.PHONY: default options all compile clean doc cleandoc test bm \
	install uninstall snapshot
