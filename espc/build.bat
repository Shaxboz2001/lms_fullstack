@echo off
set PYTHONPATH=.

pyinstaller ^
    --onefile ^
    --windowed ^
    --icon=scale.ico ^  # (опционально) добавьте иконку
    --name "KAS_Scale_Monitor" ^
    --distpath "dist_32bit" ^
    --target-architecture 32bit ^
    cas_to_exe.py