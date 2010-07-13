#!/usr/bin/env python
# -*- coding: utf-8 -*-
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

"""
Ranger - Free unix console file manager

Execute this script to start ranger.

For extended shell integration, source the file bash_integration.sh in the
top directory, passing the command to start ranger as arguments.  This only
works with the bash and zsh shell.

Example command:
source /path/to/bash_integration.sh python3 /path/to/ranger.py
"""

import ranger.slim
import sys

sys.exit(ranger.slim.main())
