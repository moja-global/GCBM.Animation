@echo off
if exist dist rd /s /q dist
if exist build rd /s /q build
if exist gcbmanimation.egg-info rd /s /q gcbmanimation.egg-info
python -m pip install --upgrade setuptools wheel
python setup.py sdist bdist_wheel
