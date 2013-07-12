#!/usr/bin/env python

# Python3 compat
from __future__ import print_function

__docformat__ = 'plaintext'

class PyRiveObjects:
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
    _objects = {} # The cache of objects loaded

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
            #self._objects[name] = RSOBJ
        except Exception as e:
            print("Failed to load code from object", name)
            print("The error given was: ", e)

    def call(self, rs, name, user, fields):
        """Invoke a previously loaded object."""
        # Call the dynamic method.
        func  = self._objects[name]
        reply = ''
        try:
            reply = func(rs, fields)
            if reply == None:
                reply = ''
        except Exception as e:
            print("Error executing Python object:", e)
            reply = '[ERR: Error when executing Python object]'
        return str(reply)
