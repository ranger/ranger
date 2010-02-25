NAME = ranger
PYTHON = python
DOCDIR = doc/pydoc
CWD = $(shell pwd)

.PHONY: all clean doc cleandoc edit push test commit install

all: clean test

doc: cleandoc
	mkdir -p $(DOCDIR)
	cd $(DOCDIR); \
		$(PYTHON) -c 'import pydoc, sys; \
		sys.path[0] = "$(CWD)"; \
		pydoc.writedocs("$(CWD)")'

install:
	@less -XF INSTALL

cleandoc:
	test -d $(DOCDIR) && rm -f $(DOCDIR)/*.html

clean:
	find . -regex .\*.py[co]$ | xargs rm

test:
	./all_tests.py

edit:
	@vi ranger.py $(shell find ranger test -regex .\*py$ )

push:
	@for repo in $(shell git remote); do \
		echo "Pushing to $$repo..."; \
		git push $$repo master; \
		git push $$repo -f hut; \
	done

commit:
	@git citool

snapshot:
	git archive HEAD | gzip > $(NAME)-$(shell git rev-list HEAD | head -n 1 | cut -b 1-16).tar.gz
