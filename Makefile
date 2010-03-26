NAME = ranger
VERSION = 1.0.4
PYTHON ?= python
DOCDIR ?= doc/pydoc
PREFIX ?= /usr/local
PYTHONOPTIMIZE ?= 2
CWD = $(shell pwd)
EDITOR ?= vim
DEST ?= $(shell $(PYTHON) -c 'import sys; sys.stdout.write( \
	[p for p in sys.path if "site" in p][0])' 2> /dev/null)/ranger

.PHONY: all compile clean doc cleandoc edit push test commit \
	install uninstall info snapshot minimal_snapshot

info:
	@echo 'This makefile provides shortcuts for common tasks.'
	@echo 'make clean: Remove all unnecessary files (.pyc, .pyo)'
	@echo 'make cleandoc: Remove the pydoc documentation'
	@echo 'make doc: Create the pydoc documentation'
	@echo 'make install: Install ranger'
	@echo 'make snapshot: Create a tar.gz of the current git revision'
	@echo
	@echo 'For developers:'
	@echo 'make commit: Test and commit the changes'
	@echo 'make test: Run all unittests.'
	@echo 'make push: push the changes via git'
	@echo 'make edit: open all relevant files in your editor'

all: test install

compile: clean
	@echo 'Compiling...'
	python -m compileall -q ranger
	PYTHONOPTIMIZE=$(PYTHONOPTIMIZE) python -m compileall -q ranger

doc: cleandoc
	mkdir -p $(DOCDIR)
	cd $(DOCDIR); \
		$(PYTHON) -c 'import pydoc, sys; \
		sys.path[0] = "$(CWD)"; \
		pydoc.writedocs("$(CWD)")'

uninstall:
	@echo 'To uninstall ranger, please remove these files:'
	@echo $(DEST)'/*'
	@echo $(PREFIX)'/bin/ranger'
	@echo 'and optionally the config files at:'
	@echo '~/.ranger'

install: compile
	@if [ '$(DEST)' == '/ranger' ]; then \
		echo 'Cannot find a suitable destination for the files.'; \
		false; \
	fi
	@echo "Installing..."
	cp ranger.py $(PREFIX)/bin/ranger
	cp -ruT ranger $(DEST)
	chmod 755 $(PREFIX)/bin/ranger
	chmod -R +rX $(DEST)
	@echo '--------------------------------------'
	@echo 'Finished.'
	@echo 'If you use BASH or ZSH, you can activate an extra feature now:'
	@echo 'When you exit ranger, the directory of the current shell can be'
	@echo 'changed to the last visited directory in ranger.  To do so, add'
	@echo 'this alias to your shell rc file (like ~/.bashrc):'
	@echo 'alias rng="source ranger ranger"'
	@echo 'And run ranger by typing rng.'


cleandoc:
	test -d $(DOCDIR) && rm -f -- $(DOCDIR)/*.html

clean:
	find . -regex [^\ ]\*.py[co]$ | xargs rm -f --

test:
	./all_tests.py 1

edit:
	@$(EDITOR) ranger.py Makefile README COPYING HACKING INSTALL $(shell find ranger test -regex .\*py$ )

push:
	@for repo in $(shell git remote); do \
		echo "Pushing to $$repo..."; \
		git push $$repo master; \
	done

commit: test
	@git citool

snapshot:
	git archive HEAD | gzip > $(NAME)-$(VERSION)-$(shell git rev-list HEAD | head -n 1 | cut -b 1-8).tar.gz

minimal_snapshot:
	@echo 'This is not quite working well. I will abort now' && false
	git checkout -b no_help
	git rm -rf doc
	git rm -rf test
	git rm all_tests.py
	git rm TODO
	git commit -a -m'removed documentation'
	git archive HEAD | gzip > $(NAME)-$(VERSION)-$(shell git rev-list HEAD | head -n 1 | cut -b 1-8).tar.gz
	git reset --hard no_help^
	git branch -D no_help
