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

Please use PGP-encryption for security-relevand patches or messages.  The UIDs
of my key are `huterich <hut@lavabit.com>` and `hut <hut@hut.pm>`, my
fingerprint is `1E9B 36EC 051F F6F7 FFC9  69A7 F08C E1E2 00FB 5CDF` and my full
pubkey is at the very bottom of this file.


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


PGP key
=======

You may wish to send the author (hut@hut.pm) PGP-encrypted mails for
security-relevant messages.  This is the authors key.  Save everything from the
`BEGIN PGP PUBLIC KEY BLOCK` up until the `END PGP PUBLIC KEY BLOCK` message
into a file and import it with `gpg --import <filename>`.

```
-----BEGIN PGP PUBLIC KEY BLOCK-----
Version: GnuPG v2

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
/Vp3S8rQGp/PJd/zIzW3VjwD4anL3g==
=n2ru
-----END PGP PUBLIC KEY BLOCK-----
```
