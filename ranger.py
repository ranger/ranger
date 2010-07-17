#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (C) 2009, 2010  Roman Zimbelmann <romanz@lavabit.com>
# This program is free software; see COPYING for details.

"""
Ranger - Free unix console file manager

Execute this script to start ranger.

For extended shell integration, source the file bash_integration.sh in the
top directory, passing the command to start ranger as arguments.  This only
works with the bash and zsh shell.

Example command:
source /path/to/bash_integration.sh python3 /path/to/ranger.py
"""

import ranger.main
import sys

sys.exit(ranger.main.main())
