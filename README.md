# AlterX - LinuxCNC GUI
Alterx - an interface for controlling milling, lathe, plasma, laser or etc. machines with a LinuxCNC (EMC2) CNC system.
Alterx is written in Python and some componets for LinuxCNC in C.

## Quick start
See the [quick start tutorial](QUICK-START.md) for a simple example on how to use AlterX. In recovery mode AlterX can be run on any desktop PC. No special hardware is required.
    
## Example
If you don't know where to start, you can find an example project in the `examples` directory. You can easily run this example in simulation mode without the need for special hardware.

<pre>
cd path/to/alterx
./examples/linuxcnc-demo_2.8/run-linuxcnc-demo.sh 
</pre>
    
## Git repository
The latest development version of AlterX can be fetched with git:

<pre>
git clone https://github.com/uncle-yura/alterx.git
cd alterx
</pre>

## Structure

The AlterX Git repository contain lots of files and directories. Here is an overview of the main files and directories and their purpose:

### Main executables
User interface executables. The main user executable is `alterx-gui`.
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
.  alterx/docs               : AlterX and LinuxCNC documentation.
.  alterx/gui                : Graphical user interface implementation (Qt).
.  alterx/configs            : Configs for create default files (INI, HAL or etc.).
.  alterx/images             : Main menu images.
.  alterx/locales            : Translation files.
.  alterx/stylesheets        : AlterX css stylesheets.
.  linuxcnc/                 : LinuxCNC componets directory.
.  menus/                    : AlterX bottom menu widgets directory.
.  tabs/                     : AlterX addons directory.
</pre>

## Dependencies
Installing AlterX on Debian based systems:
<pre>
cd path/to/alterx
sudo ./maintenance/deb-dependencies-install.sh
</pre>

To install alterx on windows you need to execute win-install-dependencies.cmd file.
Note that on windows system alterx can work only in recovery mode.

## Setup
Setup script build translated files and linuxcnc components.
<pre>
cd path/to/alterx
sudo ./setup.py
</pre>

## Usefull links
[Awlsim project by Michael Büsch](https://github.com/mbuesch/awlsim)

[QtPyVCP project by KCJ Engineering ](https://github.com/kcjengr/qtpyvcp)

[LinuxCNC project](https://github.com/LinuxCNC/linuxcnc)


## Licence / Copyright

Copyright (C) uncle-yura / et al.

AlterX is Open Source Free Software licensed under the GNU General Public License v2+. That means it's available in full source code and you are encouraged to improve it and contribute your changes back to the community. Alterx is free of charge, too. 
