# RiveScript-Python
#
# This code is released under the MIT License.
# See the "LICENSE" file for more information.
#
# https://www.rivescript.com/

# Python3 compat
from __future__ import print_function, unicode_literals
from six import text_type

class PyRiveObjects(object):
    """A RiveScript object handler for Python code.

    This class provides built-in support for your RiveScript documents to
    include and execute object macros written in Python. For example::

        > object base64 python
            import base64 as b64
            return b64.b64encode(" ".join(args))
        < object

        + encode * in base64
        - OK: <call>base64 <star></call>

    Python object macros receive these two parameters:

    * ``rs`` (RiveScript): The reference to the parent RiveScript instance.
    * ``args`` ([]str): A list of argument words passed to your object.

    Python support is on by default. To turn it off, just unset the Python
    language handler on your RiveScript object::

        rs.set_handler("python", None)
    """
    _objects = {}  # The cache of objects loaded

    def __init__(self):
        pass

    def load(self, name, code):
        """Prepare a Python code object given by the RiveScript interpreter.

        :param str name: The name of the Python object macro.
        :param []str code: The Python source code for the object macro.
        """
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
        """Invoke a previously loaded object.

        :param RiveScript rs: the parent RiveScript instance.
        :param str name: The name of the object macro to be called.
        :param str user: The user ID invoking the object macro.
        :param []str fields: Array of words sent as the object's arguments.

        :return str: The output of the object macro.
        """
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
        return text_type(reply)


class PythonObjectError(Exception):
    pass
