#!/usr/bin/env python

"""Python object macro support for RiveScript.

This class provides built-in support for your RiveScript documents to include
and execute object macros written in Python. For example:

    > object base64 python
        import base64 as b64
        return b64.b64encode(" ".join(args))
    < object

    + encode * in base64
    - OK: <call>base64 <star></call>

Python support is on by default. To turn it off, just unset the Python language
handler on your RiveScript object:

    rs.set_handler("python", None)"""

__docformat__ = 'plaintext'

class PyRiveObjects:
    """A RiveScript object handler for Python code."""
    _objects = {} # The cache of objects loaded

    def __init__(self):
        pass

    def load(self, name, code):
        """Prepare a Python code object given by the RiveScript interpreter."""
        # We need to make a dynamic Python method.
        source = "def RSOBJ(rs, args):\n"
        for line in code:
            source = source + "\t" + line + "\n"

        try:
            exec source
            self._objects[name] = RSOBJ
        except:
            print "Failed to load code from object " + name

    def call(self, rs, name, fields):
        """Invoke a previously loaded object."""
        # Call the dynamic method.
        func  = self._objects[name]
        reply = ''
        try:
            reply = func(rs, fields)
            if reply == None:
                reply = ''
        except:
            reply = '[ERR: Error when executing Python object]'
        return reply
