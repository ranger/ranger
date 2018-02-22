Prepare the "stable" branch
---------------------------
Before you can do anything else, you need to decide what should be included in
the new version.

**Bugfix releases** bump the third number of the version, e.g. 1.9.0 -> 1.9.1.
They may include bugfix commits that you `git cherry-pick`ed from the master
branch into the stable branch, or you can just do a fast-forward merge of
master into stable, if there were only bugfix commits since the last major
version.  You can also add minor new features that are very likely not causing
any bugs.  However, there should be absolutely **no** backward-incompatible
changes, like:

- renamed or removed settings, commands or python functions
- renamed, removed or reordered function arguments
- change in syntax of configuration files or in API of configuration scripts

New settings are okay, just make sure a sane default value is defined.

**Major releases** bump the second number of the version, e.g. 1.9.2 -> 1.10.0
and are necessary if you introduce any breaking changes, like the ones
mentioned in the list above.

Test everything
----------------
* [ ] `make test`
* [ ] `./ranger.py [--clean]`
* [ ] `ranger/ext/rifle.py`
* [ ] `make install`

Make a release commit
---------------------
* [ ] Update the number in the `README`
* [ ] Update `__version__` and `VERSION` in `ranger/__init__.py`
* [ ] Update `__version__` in `ranger/ext/rifle.py`
* [ ] `make man`
* [ ] Write changelog entry
* [ ] Think of a witty commit message
* [ ] Commit
* [ ] Tag the signed release with `git tag -a <commit-id>`, using the same
      commit message as annotation
* [ ] Push release and tag

Make snapshot and test again
----------------------------
* [ ] Build `.tar.gz` with `make snapshot`
* [ ] `make`
* [ ] `make install`
* [ ] Test the snapshot one last time

Update the website
------------------
* [ ] Add the new version as `ranger-stable.tar.gz`
* [ ] Add the new version as `ranger-X.Y.Z.tar.gz`
* [ ] Update both signatures `gpg --local-user 0x00FB5CDF --sign --detach-sign <file>`
* [ ] Update the man page
    * [ ] run `make manhtml` in ranger's repository
    * [ ] copy the generated `doc/ranger.1.html` to the `ranger.github.io` repository
* [ ] Rebuild the website, see `README.md` in https://github.com/ranger/ranger.github.io
* [ ] Commit & push the website

Make a PyPI release
-------------------
* [ ] `git clean --force -d -x`
* [ ] `SETUPTOOLS_USE=1 python setup.py sdist`
* [ ] `gpg --local-user 0x00000000 --detach-sign --armor dist/*`
* [ ] `twine upload dist/*`

Announce the update
-------------------
* [ ] To the mailing list
* [ ] In the arch linux forum

Change back to before
---------------------
* [ ] Change `VERSION` in `ranger/__init__.py` back to `master`
