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
* [ ] Tag signed release
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
