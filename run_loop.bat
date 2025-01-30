@echo off

if "%1"=="" (
    set PROGRAM=python .\script.py -h
    echo No arguments provided. Running help command.
    echo usage: run_loop.bat [executable] [arguments]
) else if "%1"=="-h" (
    set PROGRAM=python .\script.py -h
    echo usage: run_loop.bat [executable] [arguments]
) else if "%1"=="--help" (
    set PROGRAM=python .\script.py --help
    echo usage: run_loop.bat [executable] [arguments]
) else (
    set PROGRAM=%*
)

:loop
@REM python ".\script.py" video -o time_asc -T 5000 -D -n 1000 -B 12
@REM python ".\script.py" video -o time_asc -T 5000 
%PROGRAM%
if %errorlevel% neq 0 (
    echo An error occurred. Restarting...
    goto loop
)

echo Script has finished. 
