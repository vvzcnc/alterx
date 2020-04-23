#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# AlterX GUI - startup GUI
#
# Copyright 2020-2020 uncle-yura uncle-yura@tuta.io
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
#

from __future__ import division, absolute_import, print_function, unicode_literals

from alterx.common.compat import *
from alterx.common.util import *
from alterx.common.locale import _

from alterx.gui.util import *

import getopt


def usage():
    print(_("AlterX version {}", VERSION_STRING))
    print("")
    print(_("Usage: alterx [OPTIONS]"))
    print("")
    print(_("Options:"))
    print(_(" -h|--help             Print this help text"))
    print(_(" -L|--loglevel LVL     Set the log level:"))
    print(_("                       0: Log nothing"))
    print(_("                       1: Debug logging"))
    print(_("                       2: Log errors, warnings and info messages"))
    print(_("                       3: Log errors and warnings (default)"))
    print(_("                       4: Log errors"))
    print(_("                       5: Log critical"))
    print(_(" -l|--lang             Set locale"))


opt_loglevel = logListener.LOG_INFO
opt_lang = None
ini = None
verbose = None
try:
    if(sys.argv[1] == "-ini"):
        sys.argv[1] = "--ini"
    (opts, args) = getopt.getopt(sys.argv[1:],
                                 "vhL:l:i:",
                                 ["verbose", "help", "loglevel=", "lang=", "ini="])
except getopt.GetoptError as e:
    printError(str(e))
    usage()
    sys.exit(ExitCodes.EXIT_ERR_CMDLINE)

for (o, v) in opts:
    if o in ("-h", "--help"):
        usage()
        sys.exit(ExitCodes.EXIT_OK)
    if o in ("-L", "--loglevel"):

        try:
            opt_loglevel = int(v)
        except ValueError:
            printError("-L|--loglevel: Invalid log level")
            sys.exit(ExitCodes.EXIT_ERR_CMDLINE)
    if o in ("-l", "--lang"):
        opt_lang = str(v)
    if o in ("-v", "--verbose"):
        verbose = True
    if o in ("-i", "--ini"):
        ini = str(v)

parameters = ConfigParser()
parameters.read(ini)

try:
    log = parameters.get("DISPLAY", "LOG_FILE")
except Exception as e:
    printError(_("Get preference error: {} ", detail))

logListener.setVerbose(verbose)
logger = logListener(os.path.expanduser(log), opt_loglevel)

_.setup(opt_lang)

printVerbose(_("Loglevel: {}", opt_loglevel))

from alterx.gui.main_window import *
from alterx.common.keyboard_listener import *

qapp = QApplication(sys.argv)

printInfo(_('Using {} GUI framework', getGuiFrameworkName()))

# Create the main window.
mainwnd = MainWindow.start()
QToolTip.setFont(getDefaultFixedFont())

# Install a handler for unhandled exceptions.
def __unhandledExceptionHook(etype, value, tb):
    text = _("AlterX: ABORTING due to unhandled exception:")
    print(text, file=sys.stderr)
    __orig_excepthook(etype, value, tb)
    # Try to show an error message box.
    with suppressAllExc:
        import traceback
        QMessageBox.critical(
            None,
            _("AlterX: Unhandled exception"),
            text + "\n\n\n" +
            "".join(traceback.format_exception(etype, value, tb)),
            QMessageBox.Ok,
            QMessageBox.Ok)
    # Call QCoreApplication.exit() so that we return from exec_()
    qapp.exit(ExitCodes.EXIT_ERR_OTHER)


__orig_excepthook = sys.excepthook
sys.excepthook = __unhandledExceptionHook

# Run the main loop.
res = qapp.exec_()
sys.exit(res)
