#!/usr/bin/env python

# The MIT License (MIT)
#
# Copyright (c) 2014 Noah Petherbridge
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

from __future__ import absolute_import

"""RiveScript's __main__.py

This script is executed when you run `python rivescript` directly.
It does nothing more than load the interactive mode of RiveScript."""

__docformat__ = 'plaintext'

# Boilerplate to allow running as script directly.
# See: http://stackoverflow.com/questions/2943847/nightmare-with-relative-imports-how-does-pep-366-work
if __name__ == "__main__" and not __package__:
    import sys, os
    parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.insert(0, parent_dir)
    import rivescript
    __package__ = str("rivescript")

    from .interactive import interactive_mode
    interactive_mode()

# vim:expandtab
