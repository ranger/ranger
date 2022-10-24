Guidelines for Code Modification
================================

Coding Style
------------

* Use syntax compatible with Python `2.6+` and `3.1+`.
* Use docstrings with `pydoc` in mind
* Follow the PEP8 style guide: https://www.python.org/dev/peps/pep-0008/
* Always run `make test` before submitting a new PR. `pylint`, `flake8`,
  `pytest`, `doctest` and `shellcheck` need to be installed. (If you don't
  change any shell scripts you can run `make test_py` and you don't need the
  `shellcheck` dependency but it's an awesome tool, so check it out : )
* When breaking backward compatibility with old configuration files or plugins,
  please include a temporary workaround code that provides a compatibility
  layer and mark it with a comment that includes the word `COMPAT`. For
  examples, grep the code for the word `COMPAT`. :)


Patches
-------

Send patches, created with `git format-patch`, to the email address

    ranger-users@nongnu.org

or open a pull request on GitHub.

Please use PGP-encryption for security-relevant patches or messages. PGP key
IDs are shared along with releases on https://ranger.github.io and can be
attempted in reverse chronological order in case a maintainer is unresponsive.

Version Numbering
-----------------

Three numbers, `A.B.C`, where
* `A` changes on a rewrite
* `B` changes when major configuration incompatibilities occur
* `C` changes with each release


Starting Points
---------------

Good places to read about ranger internals are:

* `ranger/core/actions.py`
* `ranger/container/fsobject.py`

About the UI:

* `ranger/gui/widgets/browsercolumn.py`
* `ranger/gui/widgets/view_miller.py`
* `ranger/gui/ui.py`


Common Changes
==============

Adding options
--------------

* Add a default value in `rc.conf`, along with a comment that describes the option.
* Add the option to the `ALLOWED_SETTINGS` dictionary in the file
  `ranger/container/settings.py` in alphabetical order.
* Add an entry in the man page by editing `doc/ranger.pod`, then rebuild the man
  page by running `make man` in the ranger root directory

The setting is now accessible with `self.settings.my_option`, assuming self is a
subclass of `ranger.core.shared.SettingsAware`.


Adding colorschemes
-------------------

* Copy `ranger/colorschemes/default.py` to `ranger/colorschemes/myscheme.py`
  and modify it according to your needs. Alternatively, create a subclass of
  `ranger.colorschemes.default.Default` and override the `use` method, as it is
  done in the `Jungle` colorscheme.

* Add this line to your `~/.config/ranger/rc.conf`:
  `set colorscheme myscheme`


Change which programs start which file types
--------------------------------------------

Edit the configuration file `~/.config/ranger/rifle.conf`. The default one can
be obtained by running `ranger --copy-config rifle`.


Change which file extensions have which mime type
-------------------------------------------------

Modify `ranger/data/mime.types`. You may also add your own entries to `~/.mime.types`


Change which files are previewed in the auto preview
----------------------------------------------------

In `ranger/container/file.py`, change the constant `PREVIEW_BLACKLIST`
