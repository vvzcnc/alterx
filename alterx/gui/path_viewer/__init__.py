# -*- coding: utf-8 -*-
#
# AlterX GUI - VTK path viewer
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

try:
    from .vtk.path_viewer_vtk import PathViewer
except:
    try:
        from .gl.path_viewer_gl import PathViewer
    except:
        print("Error: cannot import either PathViewer VTK or GL")
        from .path_viewer import PathViewer
