#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (C) 2009, 2010  Roman Zimbelmann <romanz@lavabit.com>
# This program is free software; see COPYING for details.

"""Ranger - Free unix console file manager"""

from ranger.main import main
exit_code = main()
raise SystemExit(exit_code)
