#!/usr/bin/env python
# pyRiveScript - A RiveScript interpreter written in Python.

# Python 3 compat
from __future__ import print_function

__author__     = 'Noah Petherbridge'
__copyright__  = 'Copyright 2013, Noah Petherbridge'
__credits__    = [
    'Noah Petherbridge',
    'dinever'
]
__license__    = 'GPL'
__maintainer__ = 'Noah Petherbridge'
__status__     = 'Production'
__docformat__  = 'plaintext'

__all__      = ['rivescript']
__version__  = '1.05'

from .rivescript import RiveScript
