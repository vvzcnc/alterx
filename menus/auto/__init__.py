#!/usr/bin/env python
# -*- coding:UTF-8 -*-

from . import run
from . import pause
from . import stop
from . import step
from . import opt_stops
from . import opt_blocks
from . import from_line

buttons_order = [
    'run',
    'from_line',
    'step',
    None,
    'pause',
    'stop',
    None,
    'opt_stops',
    'opt_blocks',
]
