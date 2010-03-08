NAME = ranger
VERSION = 1.0.3
PYTHON = python
DOCDIR = doc/pydoc
CWD = $(shell pwd)
EDITOR = vim

.PHONY: all clean doc cleandoc edit push test commit install info snapshot minimal_snapshot

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

all: test

doc: cleandoc
	mkdir -p $(DOCDIR)
	cd $(DOCDIR); \
		$(PYTHON) -c 'import pydoc, sys; \
		sys.path[0] = "$(CWD)"; \
		pydoc.writedocs("$(CWD)")'

install:
	@less -XF INSTALL

cleandoc:
	test -d $(DOCDIR) && rm -f -- $(DOCDIR)/*.html

clean:
	find . -regex .\*.py[co]$ | xargs rm -f --

test: clean
	./all_tests.py

edit:
	@$(EDITOR) ranger.py Makefile README COPYING HACKING INSTALL $(shell find ranger test -regex .\*py$ )

push:
	@for repo in $(shell git remote); do \
		echo "Pushing to $$repo..."; \
		git push $$repo master; \
		git push $$repo -f hut; \
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
