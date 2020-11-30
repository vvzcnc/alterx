#!/usr/bin/env python
# -*- coding:UTF-8 -*-

from . import edit
from . import home
from . import jump_to
from . import select_file
from . import sel_next
from . import sel_prev
from . import delete_file
from . import reload_file
from . import copy_file

buttons_order = [
    'home',
    'jump_to',
    'copy_file',
    'sel_prev',
    'sel_next',
    None,
    'select_file',
    None,
    'delete_file',
    'reload_file',
    'edit',
]
