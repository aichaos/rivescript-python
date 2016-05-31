#!/usr/bin/env python

# pyRiveScript - A RiveScript interpreter written in Python.

# The MIT License (MIT)
#
# Copyright (c) 2016 Noah Petherbridge
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

# Python 3 compat
from __future__ import print_function, unicode_literals

__author__     = 'Noah Petherbridge'
__copyright__  = 'Copyright 2015, Noah Petherbridge'
__credits__    = [
    'Noah Petherbridge',
    'dinever'
]
__license__    = 'MIT'
__maintainer__ = 'Noah Petherbridge'
__status__     = 'Production'
__docformat__  = 'plaintext'

__all__      = ['rivescript']
__version__  = '1.12.2'

from .rivescript import RiveScript, RiveScriptError, NoMatchError, NoReplyError,\
    ObjectError, DeepRecursionError, NoDefaultRandomTopicError, RepliesNotSortedError
