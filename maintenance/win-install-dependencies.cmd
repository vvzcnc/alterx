@echo off
setlocal ENABLEDELAYEDEXPANSION


set PATH=%PATH%;C:\WINDOWS;C:\WINDOWS\SYSTEM32
for /D %%f in ( "C:\PYTHON*" ) do set PATH=!PATH!;%%f
for /D %%f in ( "%USERPROFILE%\AppData\Local\Programs\Python\Python*" ) do set PATH=!PATH!;%%f;%%f\Scripts


call :install pyqt5
if ERRORLEVEL 1 exit /B 1
call :install qscintilla
if ERRORLEVEL 1 exit /B 1
call :install vtk
if ERRORLEVEL 1 exit /B 1
call :install pyqtgraph
if ERRORLEVEL 1 exit /B 1
call :install polib
if ERRORLEVEL 1 exit /B 1

echo ---
echo finished successfully
pause
exit /B 0


:install
	echo Installing %1 ...
	pip3 install --upgrade %1
	if ERRORLEVEL 1 (
		echo FAILED to install %1
		pause
		exit /B 1
	)
	exit /B 0
