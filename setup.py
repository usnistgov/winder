import json, os, glob, sys

from cx_Freeze import setup, Executable
import os, sys, shutil

options = {
    "include_files" : ["apps.json"],
    "includes" : [],
    "excludes" : ["_gtkagg", "_tkagg", "bsddb", "curses", "email", "PyQt4",
            "pywin.debugger", "pywin.debugger.dbgcon", "pywin.dialogs",
            "tcl", "Tkconstants", "Tkinter","sympy","IPython"],
    "packages" : [],
    "path" : []
}

sys.argv += ['build','--build-exe=PathWinder']

includes = options['includes']
this_folder = os.path.dirname(os.path.abspath(__file__))

include_files = options['include_files']
if sys.platform == "win32":
    import win32api
    include_files += [win32api.__file__]

base = None
if sys.platform == "win32":
    base = "Win32GUI"

GUI2Exe_Target_1 = Executable(
    # what to build
    script = os.path.join(this_folder, "winder.py"),
    initScript = None,
    base = base,
    targetName = "PathWinder.exe",
    icon = None
    )

setup(
    
    version = '0.0.0',
    description = "PathWinder",
    author = "Ian Bell et al.",
    name = "Path Winder",
    
    options = {"build_exe": {"include_files": include_files,
                             "includes": includes,
                             "excludes": options['excludes'],
                             "packages": options['packages'],
                             "path": options['path']
                             }
               },
                           
    executables = [GUI2Exe_Target_1]
    )    
    
if sys.platform == "win32":
    import subprocess
    subprocess.call(r'upx/upx.exe PathWinder/*.*')
    subprocess.call(r'"C:\Program Files\7-Zip\7z" a PathWinder.zip PathWinder')
    #shutil.rmtree('PathWinder')