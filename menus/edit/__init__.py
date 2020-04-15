#!/usr/bin/env python
# -*- coding:UTF-8 -*-

from . import new_file
from . import redo
from . import replace
from . import save
from . import save_as
from . import search
from . import set_replace
from . import set_search
from . import undo

buttons_order = [
	'new_file',
	'save',
	'save_as',
	None,
	'undo',
	'redo',
	None,
	'replace',
	'set_replace',
	'search',
	'set_search',
	]
