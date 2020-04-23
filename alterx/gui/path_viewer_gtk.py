# -*- coding: utf-8 -*-
#
# AlterX GUI - path viewer
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
import rs274.glcanon
from gremlin import Gremlin
import gobject
import thread
import gtk

from alterx.common.locale import _
from alterx.common.compat import *
from alterx.common import *

from alterx.gui.util import *
from alterx.core.linuxcnc import *

import warnings

# supress 'RuntimeWarning: PyOS_InputHook is not available for interactive'
# this warning is caused by pyqt owning the Inputhook
warnings.filterwarnings("ignore")
warnings.filterwarnings("default")


gobject.threads_init()

# Using a separate thread for GTK


def run_gtk(self):
    try:
        gtk.gdk.threads_enter()
        gtk.main()
        gtk.gdk.threads_leave()
    except:
        pass


class modded_gremlin(Gremlin):
    def __init__(self,  *a, **kw):
        Gremlin.__init__(self, INI)
        self._reload_filename = None
        self.enable_dro = True
        self.colors['overlay_background'] = (0.0, 0.0, 0.0)
        self.colors['back'] = (0.0, 0.0, 0.0)

    def set_metric_units(self, state):
        self.metric_units = state
        self.expose()

    def set_spindle_speed(self, rate):
        if rate < 1:
            rate = 1
        self.spindle_speed = rate

    def setview(self, value):
        view = str(value).lower()
        if self.lathe_option:
            if view not in ['p', 'y', 'y2']:
                return False
        elif view not in ['p', 'x', 'y', 'z', 'z2']:
            return False
        self.current_view = view
        if self.initialised:
            self.set_current_view()

    def reloadfile(self, w):
        dist = self.get_zoom_distance()
        try:
            self.fileloaded(self._reload_filename)
            self.set_zoom_distance(dist)
        except Exception as e:
            printError(_('HAL Gremlin reload error: {}', e))
            pass

    def fileloaded(self, f):
        self._reload_filename = f
        try:
            self._load(f)
        except AttributeError as e:
            # AttributeError: 'NoneType' object has no attribute 'gl_end'
            printError(_('HAL Gremlin continuing after exception'))

    @rs274.glcanon.with_context
    def _load(self, filename):
        return self.load(filename)

    # Override gremlin's / glcannon.py function so we can emit a GObject signal
    def update_highlight_variable(self, line):
        self.highlight_line = line
        if line == None:
            line = -1
        printDebug(_('Highlighting line in graphics: {}', line))

    # This overrides glcannon.py method so we can change the DRO
    def dro_format(self, s, spd, dtg, limit, homed, positions, axisdtg, g5x_offset, g92_offset, tlo_offset):
        if not self.enable_dro:
            return limit, homed, [''], ['']

        if self.metric_units:
            format = "% 6s:% 9.3f"
            if self.show_dtg:
                droformat = " " + format + "  DTG %1s:% 9.3f"
            else:
                droformat = " " + format
            offsetformat = "% 5s %1s:% 9.3f  G92 %1s:% 9.3f"
            rotformat = "% 5s %1s:% 9.3f"
        else:
            format = "% 6s:% 9.4f"
            if self.show_dtg:
                droformat = " " + format + "  DTG %1s:% 9.4f"
            else:
                droformat = " " + format
            offsetformat = "% 5s %1s:% 9.4f  G92 %1s:% 9.4f"
            rotformat = "% 5s %1s:% 9.4f"
        diaformat = " " + format

        posstrs = []
        droposstrs = []
        for i in range(9):
            a = "XYZABCUVW"[i]
            if s.axis_mask & (1 << i):
                posstrs.append(format % (a, positions[i]))
                if self.show_dtg:
                    droposstrs.append(droformat %
                                      (a, positions[i], a, axisdtg[i]))
                else:
                    droposstrs.append(droformat % (a, positions[i]))
        droposstrs.append("")

        for i in range(9):
            index = s.g5x_index
            if index < 7:
                label = "G5%d" % (index+3)
            else:
                label = "G59.%d" % (index-6)

            a = "XYZABCUVW"[i]
            if s.axis_mask & (1 << i):
                droposstrs.append(offsetformat %
                                  (label, a, g5x_offset[i], a, g92_offset[i]))
        droposstrs.append(rotformat % (label, 'R', s.rotation_xy))

        droposstrs.append("")
        for i in range(9):
            a = "XYZABCUVW"[i]
            if s.axis_mask & (1 << i):
                droposstrs.append(rotformat % ("TLO", a, tlo_offset[i]))

        # if its a lathe only show radius or diameter as per property
        # we have to adjust the homing icon to line up:
        if self.is_lathe():
            if homed[0]:
                homed.pop(0)
                homed.pop(0)
                homed.insert(0, 1)
                homed.insert(0, 0)
            posstrs[0] = ""
            if self.show_lathe_radius:
                posstrs.insert(1, format % ("Rad", positions[0]))
            else:
                posstrs.insert(1, format % ("Dia", positions[0]*2.0))
            droposstrs[0] = ""
            if self.show_dtg:
                if self.show_lathe_radius:
                    droposstrs.insert(1, droformat %
                                      ("Rad", positions[0], "R", axisdtg[0]))
                else:
                    droposstrs.insert(1, droformat % (
                        "Dia", positions[0]*2.0, "D", axisdtg[0]*2.0))
            else:
                if self.show_lathe_radius:
                    droposstrs.insert(1, droformat % ("Rad", positions[0]))
                else:
                    droposstrs.insert(1, diaformat % ("Dia", positions[0]*2.0))

        if self.show_velocity:
            if self.is_lathe():
                pos = 1
                posstrs.append(format % ("IPR", spd/abs(self.spindle_speed)))
            else:
                pos = 0
                posstrs.append(format % ("Vel", spd))

            for i in range(9):
                if s.axis_mask & (1 << i):
                    pos += 1

            droposstrs.insert(pos, " " + format % ("Vel", spd))

        if self.show_dtg:
            posstrs.append(format % ("DTG", dtg))

        return limit, homed, posstrs, droposstrs

###############################################
# GTK Plug Class
# This is the GTK embedding plug that will
# put the modded gremlin object into.
# This get embedded into a QT container
# It runs in it's own thread to update the
# GTK side of things
###############################################


class PyApp(gtk.Plug):
    def __init__(self, Wid):
        gtk.Plug.__init__(self, Wid)
        self.connect("destroy", self.on_destroy)
        self.plug_id = self.get_id()
        vbox = gtk.VBox()
        self.add(vbox)
        self.gremlin = modded_gremlin()
        vbox.add(self.gremlin)

        self.show_all()

    def on_destroy(self, w):
        try:
            gtk.gdk.threads_enter()
            gtk.main_quit()
            gtk.gdk.threads_leave()
        except:
            pass

##############################################
# Container class
# We embed Gremlin GTK object into this
##############################################


class PathViewer(QWidget):
    def __init__(self, parent=None):
        QWidget.__init__(self, parent)
        self.pygtk = PyApp(0l)
        self.gremlin = self.pygtk.gremlin
        # run GTK in a separate thread
        try:
            thread.start_new_thread(run_gtk, (None))
        except:
            pass

        # embed GTK gremlin
        self.embed_plug(self.pygtk.plug_id)

        self.gremlin.metric_units = False
        self.setview('p')

        UPDATER.add("display-clear")
        UPDATER.add("display-view-p")
        UPDATER.add("display-view-x")
        UPDATER.add("display-view-y")
        UPDATER.add("display-view-z")
        UPDATER.add("display-view-zp")
        UPDATER.add("display-view-zm")

        UPDATER.connect("display-clear", lambda s: self.clear_plot())
        UPDATER.connect("display-view-p", lambda s: self.setview('p'))
        UPDATER.connect("display-view-x", lambda s: self.setview('x'))
        UPDATER.connect("display-view-y", lambda s: self.setview('y'))
        UPDATER.connect("display-view-z", lambda s: self.setview('z'))
        UPDATER.connect("display-view-zp", lambda s: self.zoomin())
        UPDATER.connect("display-view-zm", lambda s: self.zoomout())

        UPDATER.connect("file", self.load)

    # Embed a X11 window into a QT window using X window ID

    def embed_plug(self, WID):
        self.haveContainer = True
        subWindow = QWindow.fromWinId(WID)
        container = self.createWindowContainer(subWindow)
        container.setParent(self)
        container.show()
        container.resize(330, 360)

    def sizeHint(self):
        return QSize(300, 300)

    def closeEvent(self, event):
        self.pygtk.on_destroy(None)

    def event(self, event):
        if event.type() == QEvent.Resize:
            w = QResizeEvent.size(event)
            self.gremlin.set_size_request(w.width(), w.height())
            # self.resize(QResizeEvent.size(event))
        return True

    # property getter/setters
    # FILE
    def load(self, file):
        self.gremlin._reload_filename = file
        self.gremlin.reloadfile(None)

    # ZOOM
    def zoomin(self):
        self.gremlin.zoomin()

    def zoomout(self):
        self.gremlin.zoomout()

    # PLOT
    def clear_plot(self):
        self.gremlin.clear_live_plotter()

    # VIEW
    def setview(self, view):
        self.gremlin.setview(view)

    def getview(self):
        return self.gremlin.current_view

    def resetview(self):
        self.gremlin.setview('p')

    # DRO
    def setdro(self, state):
        self.gremlin.enable_dro = state
        self.gremlin.expose()

    def getdro(self):
        return self.gremlin.enable_dro

    # DTG
    def setdtg(self, state):
        self.gremlin.show_dtg = state
        self.gremlin.expose()

    def getdtg(self):
        return self.gremlin.show_dtg

    # METRIC
    def setmetric(self, state):
        self.gremlin.metric_units = state
        self.gremlin.expose()

    def getmetric(self):
        return self.gremlin.metric_units
