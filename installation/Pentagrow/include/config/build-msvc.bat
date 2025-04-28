
set TARGET_ARCH=intel64
if /i "%1"=="ia32" (set TARGET_ARCH=ia32)

set JOM="C:\Qt\qtcreator-3.3.2\bin\jom.exe"

if /i "%TARGET_ARCH%"=="intel64" (set QMAKE="C:\Qt\qt-5.3.2-vs2013-64bit\qtbase\bin\qmake.exe")
if /i "%TARGET_ARCH%"=="ia32"    (set QMAKE="C:\Qt\qt-5.3.2-vs2013-32bit\qtbase\bin\qmake.exe")

if /i "%TARGET_ARCH%"=="intel64" (set BIN_DIR="..\..\bin64")
if /i "%TARGET_ARCH%"=="ia32" (set BIN_DIR="..\..\bin32")

cd boost
@call %QMAKE% -spec win32-msvc2013 CONFIG+=preset-vzm CONFIG+=release CONFIG-=debug
@call %JOM% clean
@call %JOM%

cd ..\genua
@call %QMAKE% -spec win32-msvc2013 CONFIG+=preset-vzm CONFIG+=release CONFIG-=debug
@call %JOM% clean
@call %JOM%

cd ..\predicates
@call %QMAKE%  -spec win32-msvc2013  CONFIG+=preset-vzm  CONFIG+=release CONFIG-=debug
@call %JOM% clean
@call %JOM%

cd ..\surf
@call %QMAKE%  -spec win32-msvc2013  CONFIG+=preset-vzm CONFIG+=release CONFIG-=debug
@call %JOM% clean
@call %JOM%

cd ..\qcustomplot
@call %QMAKE%  -spec win32-msvc2013  CONFIG+=preset-vzm CONFIG+=release CONFIG-=debug
@call %JOM% clean
@call %JOM%

cd ..\lima
@call %QMAKE%  -spec win32-msvc2013  CONFIG+=preset-vzm CONFIG+=release CONFIG-=debug
@call %JOM% clean
@call %JOM%

cd ..\QGLViewer\QGLViewer
@call %QMAKE%  -spec win32-msvc2013  CONFIG+=preset-vzm CONFIG+=release CONFIG-=debug
@call %JOM% clean
@call %JOM%

cd ..\..\vzm
del Makefile* 
del app\Makefile* 
del yaobi\Makefile* 
del sse\Makefile* 
del avx\Makefile* 
del fma\Makefile*
@call %QMAKE% -spec win32-msvc2013 CONFIG+=release CONFIG-=debug CONFIG+=preset-vzm CONFIG-=vzm-player CONFIG*=vzm-lima
@call %JOM% clean
@call %JOM%

cd ..\..\vzm
del Makefile* 
del app\Makefile* 
del yaobi\Makefile* 
del sse\Makefile* 
del avx\Makefile* 
del fma\Makefile*
@call %QMAKE% -spec win32-msvc2013 CONFIG+=release CONFIG-=debug CONFIG+=preset-vzm CONFIG+=vzm-player CONFIG-=vzm-lima
@call %JOM% clean
@call %JOM%

cd %BIN_DIR%
@call mt -manifest vzm.exe.embed.manifest -outputresource:vzm.exe;1
@call mt -manifest vzmplayer.exe.embed.manifest -outputresource:vzmplayer.exe;1

