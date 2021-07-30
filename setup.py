#!/usr/bin/env python

import polib
import os
import sys

isWindows = os.name.lower() in {"nt", "ce"}
isPosix = os.name.lower() == "posix"

def create_mo_files(dir):
    package_files = []
    po_dirs = [os.path.join('locales',l,'LC_MESSAGES')
               for l in next(os.walk(os.path.join(dir,"alterx","locales")))[1]]
    for d in po_dirs:
        po_files = [f
                    for f in next(os.walk(os.path.join(dir,"alterx",d)))[2]
                    if os.path.splitext(f)[1] == '.po']  
        for po_file in po_files:
            filename, extension = os.path.splitext(po_file)
            mo_file = filename + '.mo'
            pf = polib.pofile(os.path.join(dir,"alterx",d, po_file))
            pf.save_as_mofile(os.path.join(dir,"alterx",d, mo_file))
            package_files.append(os.path.join(d, mo_file))
    return package_files

dir_path = os.path.dirname(os.path.realpath(__file__))

if isPosix:
    os.system("cd "+dir_path+";sh "+os.path.join(dir_path,"maintenance","comp_install.sh"))

create_mo_files(dir_path)

