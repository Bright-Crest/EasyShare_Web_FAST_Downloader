@echo off

cd /d %~dp0

REM SCRIPT PATH
set SP=.\script.py

echo Testing download home
start "home" python "%SP%" home -D

echo Testing download img
start "img" python "%SP%" img -D

echo Testing download video
start "video" python "%SP%" video -D

echo Testing download music
start "music" python "%SP%" music -D

echo Testing download doc
start "doc" python "%SP%" doc -D
