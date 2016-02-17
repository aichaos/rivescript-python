#!/usr/bin/env python

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

# Python3 compat
from __future__ import print_function, unicode_literals

__docformat__ = 'plaintext'


class PyRiveObjects(object):
    """A RiveScript object handler for Python code.

This class provides built-in support for your RiveScript documents to include
and execute object macros written in Python. For example:

    > object base64 python
        import base64 as b64
        return b64.b64encode(" ".join(args))
    < object

    + encode * in base64
    - OK: <call>base64 <star></call>

Python object macros receive these two parameters:

    rs:   The reference to the parent RiveScript instance
    args: A list of argument words passed to your object macro

Python support is on by default. To turn it off, just unset the Python language
handler on your RiveScript object:

    rs.set_handler("python", None)"""
    _objects = {}  # The cache of objects loaded

    def __init__(self):
        pass

    def load(self, name, code):
        """Prepare a Python code object given by the RiveScript interpreter."""
        # We need to make a dynamic Python method.
        source = "def RSOBJ(rs, args):\n"
        for line in code:
            source = source + "\t" + line + "\n"

        source += "self._objects[name] = RSOBJ\n"

        try:
            exec(source)
            # self._objects[name] = RSOBJ
        except Exception as e:
            print("Failed to load code from object", name)
            print("The error given was: ", e)

    def call(self, rs, name, user, fields):
        """Invoke a previously loaded object."""
        # Call the dynamic method.
        if name not in self._objects:
            return '[ERR: Object Not Found]'
        func = self._objects[name]
        reply = ''
        try:
            reply = func(rs, fields)
            if reply is None:
                reply = ''
        except Exception as e:
            raise PythonObjectError("Error executing Python object: " + str(e))
        return str(reply)


class PythonObjectError(Exception):
    pass