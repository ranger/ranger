#!/usr/bin/python

import os.path
import re
import sys


# Add relevant ranger module to PATH... there surely is a better way to do this...
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


def test(boolean, errormessage):
    if not boolean:
        sys.stderr.write('TEST FAILURE: ')
        sys.stderr.write(errormessage)
        sys.stderr.write('\n')
        sys.stderr.flush()


def get_path_of_man_page():
    dirpath_of_this_file = os.path.dirname(__file__)
    return os.path.join(dirpath_of_this_file, '..', 'doc', 'ranger.pod')


def read_manpage():
    path = get_path_of_man_page()
    return open(path, 'r').read()


def get_sections():
    manpage = read_manpage()
    parts = manpage.split('=head1 ')
    sections = dict()
    for part in parts:
        if '\n' in part:
            section_name, section_content = part.split('\n', 1)
            sections[section_name] = section_content
        else:
            pass
    return sections


def check_if_settings_are_documented():
    from ranger.container.settings import ALLOWED_SETTINGS
    sections = get_sections()
    setting_section = sections['SETTINGS']
    matcher_pattern = r'^=item [\w\d_, ]*{setting}'
    for setting in ALLOWED_SETTINGS:
        matcher = re.compile(matcher_pattern.format(setting=setting), re.M)
        test(matcher.search(setting_section), ('Setting %s is not documented in the man page!' % setting))


if __name__ == '__main__':
    check_if_settings_are_documented()
