Guidelines for Code Modification
================================

Coding Style
------------

* Use syntax compatible to both python 2.6+ and 3.1+.
* Use docstrings with pydoc in mind
* Follow the style guide for python code:
    http://www.python.org/dev/peps/pep-0008/
* Test the code with "doctest" where it makes sense


Patches
-------

Send patches, created with "git format-patch", to the email address

    hut@hut.pm

or open a pull request on GitHub.


Version Numbering
-----------------

Three numbers, A.B.C, where
* A changes on a rewrite
* B changes when major configuration incompatibilities occur
* C changes with each release


Starting Points
---------------

Good places to read about ranger internals are:

* ranger/core/actions.py
* ranger/container/fsobject.py

About the UI:

* ranger/gui/widgets/browsercolumn.py
* ranger/gui/widgets/browserview.py
* ranger/gui/ui.py


Common Changes
==============

Adding options
--------------

* Add a default value in rc.conf, along with a comment that describes the option.
* Add the option to the ALLOWED_SETTINGS dictionary in the file
  ranger/container/settings.py.  Make sure to sort in the new entry
  alphabetically.
* Add an entry in the man page by editing doc/ranger.pod, then rebuild the man
  page by running "make man" in the ranger root directory

The setting is now accessible with self.settings.my_option, assuming self is a
subclass of ranger.core.shared.SettingsAware.


Adding colorschemes
-------------------

* Copy ranger/colorschemes/default.py to ranger/colorschemes/myscheme.py
  and modify it according to your needs.  Alternatively, create a subclass of
  ranger.colorschemes.default.Default and override the "use" method, as it is
  done in the "Jungle" colorscheme.

* Add this line to your ~/.config/ranger/rc.conf:

    set colorscheme myscheme


Change which programs start which file types
--------------------------------------------

Edit the configuration file ~/.config/ranger/rifle.conf.  The default one can
be obtained by running "ranger --copy-config rifle".


Change which file extensions have which mime type
-------------------------------------------------

Modify ranger/data/mime.types.  You may also add your own entries to ~/.mime.types


Change which files are previewed in the auto preview
----------------------------------------------------

In ranger/container/file.py, change the constant PREVIEW_BLACKLIST
