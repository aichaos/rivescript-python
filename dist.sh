#!/bin/bash

# Prepare the module for distribution.
python setup.py bdist_rpm --packager="Noah Petherbridge <root@kirsle.net>" \
	bdist_wininst --plat-name=win32 \
	bdist_dumb
