@echo off
call "C:\Program Files\Microsoft Visual Studio\18\Community\VC\Auxiliary\Build\vcvars64.bat"
cd /d "%~dp0"
cl /nologo /O2 /I "C:\Users\q3726\Downloads\blender-main\extern\nanosvg" nanosvg_rasterize.c /Fe:nanosvg_rasterize.exe
