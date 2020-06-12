# AlterX - LinuxCNC GUI
Alterx - an interface for controlling milling, lathe, plasma, laser or etc. machines with a LinuxCNC (EMC2) CNC system.
Alterx is written in Python and some componets for LinuxCNC in C.

## Quick start
    pass
    
## Example
    pass
    
## Git repository
The latest development version of AlterX can be fetched with git:

<pre>
git https://github.com/uncle-yura/alterx.git
cd alterx
</pre>

## Structure

The AlterX Git repository contain lots of files and directories. Here is an overview of the main files and directories and their purpose:

### Main executables
User interface executables. The main user executable is `awlsim-gui`.
<pre>
.  alterx-gui                : Graphical user interface. This is the main user frontend.
.  ascope-gui                : Standalone ascope component.
</pre>

### Documentation
These files and directories contain useful information about AlterX.
<pre>
.  examples/                 : Various example projects and feature demonstrations.
.  LICENCE                   : Main license.
.  QUICK-START.md            : Quick start tutorial.
.  README.md                 : Main README document.
.  TODO.md                   : TODO list.
</pre>

### Main modules
The main modules implement most of AlterX's functionality.
<pre>
.  alterx/                   : Main AlterX Python-module directory.
.  alterx/common             : Common libraries, modules and helper functions.
.  alterx/core               : AlterX core. This is where the LinuxCNC data is processing.
.  alterx/gui                : Graphical user interface implementation (Qt).
.  alterx/configs            : Configs for create default files (INI, HAL or etc.).
.  alterx/images             : Main menu images.
.  alterx/stylesheets        : AlterX css stylesheets.
.  linuxcnc/                 : LinuxCNC componets directory.
.  menus/                    : AlterX bottom menu widgets directory.
.  tabs/                     : AlterX addons directory.
</pre>

## Dependencies
    pass

## Build
    pass

## Licence / Copyright

Copyright (C) uncle-yura / et al.

AlterX is Open Source Free Software licensed under the GNU General Public License v2+. That means it's available in full source code and you are encouraged to improve it and contribute your changes back to the community. Alterx is free of charge, too. 
