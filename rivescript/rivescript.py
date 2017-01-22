# RiveScript-Python
#
# This code is released under the MIT License.
# See the "LICENSE" file for more information.
#
# https://www.rivescript.com/

from __future__ import unicode_literals
from six import text_type
import sys
import os
import re
import pprint
import codecs

from . import __version__
from . import python
from . import sorting
from . import inheritance as inherit_utils
from . import utils
from .brain import Brain
from .parser import Parser
from .sessions import MemorySessionStorage
from .exceptions import (
    RS_ERR_MATCH, RS_ERR_REPLY, RS_ERR_DEEP_RECURSION
)

# These constants come from the exceptions submodule but should be exportable
# from this one. Pyflakes gives warnings about them not being used, so...
_ = RS_ERR_MATCH
_ = RS_ERR_REPLY
_ = RS_ERR_DEEP_RECURSION

class RiveScript(object):
    """A RiveScript interpreter for Python 2 and 3.

    Parameters:
        debug (bool): Set to ``True`` to enable verbose logging to standard out.
        strict (bool): Enable strict mode. Strict mode causes RiveScript syntax
            errors to raise an exception at parse time. Strict mode is on
            (``True``) by default.
        log (str or fh): Specify a path to a file or a filehandle opened in
            write mode to direct log output to. This can send debug logging to
            a file rather than to ``STDOUT``.
        depth (int): Set the recursion depth limit. This is how many times
            RiveScript will recursively follow redirects before giving up with
            a ``DeepRecursionError`` exception. The default is ``50``.
        utf8 (bool): Enable UTF-8 mode. When this mode is enabled, triggers in
            RiveScript code are permitted to contain foreign and special
            symbols. Additionally, user messages are allowed to contain most
            symbols instead of having all symbols stripped away. This is
            considered an experimental feature because all of the edge cases of
            supporting Unicode haven't been fully tested. This option
            is ``False`` by default.
        session_manager (SessionManager): By default RiveScript uses an
            in-memory session manager to keep track of user variables and state
            information. If you have your own session manager that you'd like
            to use instead, pass its instantiated class instance as this
            parameter.
    """

    ############################################################################
    # Initialization and Utility Methods                                       #
    ############################################################################

    def __init__(self, debug=False, strict=True, depth=50, log=None,
                 utf8=False, session_manager=None):
        """Initialize a new RiveScript interpreter."""

        ###
        # User configurable fields.
        ###

        # Debugging
        self._debug = debug   # Debug mode
        self._log   = log     # Debug log file.

        # If the log file was given as a string, turn it into a filehandle.
        if log is not None:
            if type(log) in [text_type, str]:
                self._log = codecs.open(log, "a", "utf-8")

        # Unicode stuff
        self._utf8               = utf8  # UTF-8 mode
        self.unicode_punctuation = re.compile(r'[.,!?;:]')

        # Misc.
        self._strict = strict  # Strict mode
        self._depth  = depth   # Recursion depth limit

        ###
        # Internal fields.
        ###
        self._global   = {}      # 'global' variables
        self._var      = {}      # 'bot' variables
        self._sub      = {}      # 'sub' variables
        self._person   = {}      # 'person' variables
        self._array    = {}      # 'array' variables
        self._includes = {}      # included topics
        self._lineage  = {}      # inherited topics
        self._handlers = {}      # Object handlers
        self._objlangs = {}      # Languages of objects used
        self._topics   = {}      # Main reply structure
        self._thats    = {}      # %Previous reply structure
        self._sorted   = {}      # Sorted buffers
        self._syntax   = {}      # Syntax tracking (filenames & line no.'s)
        self._regexc   = {       # Precomputed regexes for speed optimizations.
            "trigger": {},
            "sub":    {},
            "person":  {},
        }
        
        # Initialize the session manager.
        if session_manager is None:
            session_manager = MemorySessionStorage(warn=self._warn)
        self._session  = session_manager

        # Internal helpers.
        self._parser = Parser(
            strict=self._strict,
            utf8=self._utf8,
            on_debug=lambda message: self._say(message),
            on_warn=lambda message, filename, lineno: self._warn(message, filename, lineno),
        )
        self._brain = Brain(
            master=self,
            strict=self._strict,
            utf8=self._utf8,
        )

        # Define the default Python language handler.
        self._handlers["python"] = python.PyRiveObjects()

        self._say("Interpreter initialized.")

    @classmethod
    def VERSION(self=None):
        """Return the version number of the RiveScript library.

        This may be called as either a class method or a method of a RiveScript
        object instance."""
        return __version__

    def _say(self, message):
        if self._debug and not self._log:
            print("[RS] {}".format(message))
        if self._log:
            # Log it to the file.
            self._log.write("[RS] " + message + "\n")

    def _warn(self, message, fname='', lineno=0):
        header = "[RS]"
        if self._debug:
            header = "[RS::Warning]"
        if len(fname) and lineno > 0:
            print(header, message, "at", fname, "line", lineno)
        else:
            print(header, message)

    ############################################################################
    # Loading and Parsing Methods                                              #
    ############################################################################

    def load_directory(self, directory, ext=None):
        """Load RiveScript documents from a directory.

        :param str directory: The directory of RiveScript documents to load
            replies from.
        :param []str ext: List of file extensions to consider as RiveScript
            documents. The default is ``[".rive", ".rs"]``.
        """
        self._say("Loading from directory: " + directory)

        if ext is None:
            # Use the default extensions - .rive is preferable.
            ext = ['.rive', '.rs']
        elif type(ext) == str:
            # Backwards compatibility for ext being a string value.
            ext = [ext]

        if not os.path.isdir(directory):
            self._warn("Error: " + directory + " is not a directory.")
            return

        for root, subdirs, files in os.walk(directory):
            for file in files:
                for extension in ext:
                    if file.lower().endswith(extension):
                        # Load this file.
                        self.load_file(os.path.join(root, file))
                        break

    def load_file(self, filename):
        """Load and parse a RiveScript document.

        :param str filename: The path to a RiveScript file.
        """
        self._say("Loading file: " + filename)

        fh    = codecs.open(filename, 'r', 'utf-8')
        lines = fh.readlines()
        fh.close()

        self._say("Parsing " + str(len(lines)) + " lines of code from " + filename)
        self._parse(filename, lines)

    def stream(self, code):
        """Stream in RiveScript source code dynamically.

        :param code: Either a string containing RiveScript code or an array of
            lines of RiveScript code.
        """
        self._say("Streaming code.")
        if type(code) in [str, text_type]:
            code = code.split("\n")
        self._parse("stream()", code)

    def _parse(self, fname, code):
        """Parse RiveScript code into memory.

        :param str fname: The arbitrary file name used for syntax reporting.
        :param []str code: Lines of RiveScript source code to parse.
        """

        # Get the "abstract syntax tree"
        ast = self._parser.parse(fname, code)

        # Get all of the "begin" type variables: global, var, sub, person, ...
        for kind, data in ast["begin"].items():
            internal = getattr(self, "_" + kind)  # The internal name for this attribute
            for name, value in data.items():
                if value == "<undef>":
                    del internal[name]
                else:
                    internal[name] = value

                # Precompile substitutions.
                if kind in ["sub", "person"]:
                    self._precompile_substitution(kind, name)

        # Let the scripts set the debug mode and other special globals.
        if self._global.get("debug"):
            self._debug = str(self._global["debug"]).lower() == "true"
        if self._global.get("depth"):
            self._depth = int(self._global["depth"])

        # Consume all the parsed triggers.
        for topic, data in ast["topics"].items():
            # Keep a map of the topics that are included/inherited under this topic.
            if not topic in self._includes:
                self._includes[topic] = {}
            if not topic in self._lineage:
                self._lineage[topic] = {}
            self._includes[topic].update(data["includes"])
            self._lineage[topic].update(data["inherits"])

            # Consume the triggers.
            if not topic in self._topics:
                self._topics[topic] = []
            for trigger in data["triggers"]:
                self._topics[topic].append(trigger)

                # Precompile the regexp for this trigger.
                self._precompile_regexp(trigger["trigger"])

                # Does this trigger have a %Previous? If so, make a pointer to
                # this exact trigger in _thats.
                if trigger["previous"] is not None:
                    if not topic in self._thats:
                        self._thats[topic] = {}
                    if not trigger["trigger"] in self._thats[topic]:
                        self._thats[topic][trigger["trigger"]] = {}
                    self._thats[topic][trigger["trigger"]][trigger["previous"]] = trigger

        # Load all the parsed objects.
        for obj in ast["objects"]:
            # Have a handler for it?
            if obj["language"] in self._handlers:
                self._objlangs[obj["name"]] = obj["language"]
                self._handlers[obj["language"]].load(obj["name"], obj["code"])

    def deparse(self):
        """Dump the in-memory RiveScript brain as a Python data structure.

        This would be useful, for example, to develop a user interface for
        editing RiveScript replies without having to edit the RiveScript
        source code directly.

        :return dict: JSON-serializable Python data structure containing the
            contents of all RiveScript replies currently loaded in memory.
        """

        # Data to return.
        result = {
            "begin": {
                "global":   {},
                "var":      {},
                "sub":      {},
                "person":   {},
                "array":    {},
                "triggers": {},
                "that": {},
            },
            "topic":   {},
            "that":    {},
            "inherit": {},
            "include": {},
        }

        # Populate the config fields.
        if self._debug:
            result["begin"]["global"]["debug"] = self._debug
        if self._depth != 50:
            result["begin"]["global"]["depth"] = 50

        # Definitions
        result["begin"]["var"]    = self._var.copy()
        result["begin"]["sub"]    = self._sub.copy()
        result["begin"]["person"] = self._person.copy()
        result["begin"]["array"]  = self._array.copy()
        result["begin"]["global"].update(self._global.copy())

        # Topic Triggers.
        for topic in self._topics:
            dest = {}  # Where to place the topic info

            if topic == "__begin__":
                # Begin block.
                dest = result["begin"]["triggers"]
            else:
                # Normal topic.
                if topic not in result["topic"]:
                    result["topic"][topic] = {}
                dest = result["topic"][topic]

            # Copy the triggers.
            for trig, data in self._topics[topic].iteritems():
                dest[trig] = self._copy_trigger(trig, data)

        # %Previous's.
        for topic in self._thats:
            dest = {}  # Where to place the topic info

            if topic == "__begin__":
                # Begin block.
                dest = result["begin"]["that"]
            else:
                # Normal topic.
                if topic not in result["that"]:
                    result["that"][topic] = {}
                dest = result["that"][topic]

            # The "that" structure is backwards: bot reply, then trigger, then info.
            for previous, pdata in self._thats[topic].iteritems():
                for trig, data in pdata.iteritems():
                    dest[trig] = self._copy_trigger(trig, data, previous)

        # Inherits/Includes.
        for topic, data in self._lineage.iteritems():
            result["inherit"][topic] = []
            for inherit in data:
                result["inherit"][topic].append(inherit)
        for topic, data in self._includes.iteritems():
            result["include"][topic] = []
            for include in data:
                result["include"][topic].append(include)

        return result

    def write(self, fh, deparsed=None):
        """Write the currently parsed RiveScript data into a file.

        Pass either a file name (string) or a file handle object.

        This uses ``deparse()`` to dump a representation of the loaded data and
        writes it to the destination file. If you provide your own data as the
        ``deparsed`` argument, it will use that data instead of calling
        ``deparse()`` itself. This way you can use ``deparse()``, edit the data,
        and use that to write the RiveScript document (for example, to be used
        by a user interface for editing RiveScript without writing the code
        directly).

        :param fh: Either a file name ``str`` or a file handle object of a file
            opened in write mode.
        :param optional dict deparsed: A data structure in the same format as
            what ``deparse()`` returns. If not passed, this value will come from
            the current in-memory data from ``deparse()``.
        """

        # Passed a string instead of a file handle?
        if type(fh) is str:
            fh = codecs.open(fh, "w", "utf-8")

        # Deparse the loaded data.
        if deparsed is None:
            deparsed = self.deparse()

        # Start at the beginning.
        fh.write("// Written by rivescript.deparse()\n")
        fh.write("! version = 2.0\n\n")

        # Variables of all sorts!
        for kind in ["global", "var", "sub", "person", "array"]:
            if len(deparsed["begin"][kind].keys()) == 0:
                continue

            for var in sorted(deparsed["begin"][kind].keys()):
                # Array types need to be separated by either spaces or pipes.
                data = deparsed["begin"][kind][var]
                if type(data) not in [str, text_type]:
                    needs_pipes = False
                    for test in data:
                        if " " in test:
                            needs_pipes = True
                            break

                    # Word-wrap the result, target width is 78 chars minus the
                    # kind, var, and spaces and equals sign.
                    # TODO: not implemented yet.
                    # width = 78 - len(kind) - len(var) - 4

                    if needs_pipes:
                        data = self._write_wrapped("|".join(data), sep="|")
                    else:
                        data = " ".join(data)

                fh.write("! {kind} {var} = {data}\n".format(
                    kind=kind,
                    var=var,
                    data=data,
                ))
            fh.write("\n")

        # Begin block.
        if len(deparsed["begin"]["triggers"].keys()):
            fh.write("> begin\n\n")
            self._write_triggers(fh, deparsed["begin"]["triggers"], indent="\t")
            fh.write("< begin\n\n")

        # The topics. Random first!
        topics = ["random"]
        topics.extend(sorted(deparsed["topic"].keys()))
        done_random = False
        for topic in topics:
            if topic not in deparsed["topic"]: continue
            if topic == "random" and done_random: continue
            if topic == "random": done_random = True

            tagged = False  # Used > topic tag

            if topic != "random" or topic in deparsed["include"] or topic in deparsed["inherit"]:
                tagged = True
                fh.write("> topic " + topic)

                if topic in deparsed["inherit"]:
                    fh.write(" inherits " + " ".join(deparsed["inherit"][topic]))
                if topic in deparsed["include"]:
                    fh.write(" includes " + " ".join(deparsed["include"][topic]))

                fh.write("\n\n")

            indent = "\t" if tagged else ""
            self._write_triggers(fh, deparsed["topic"][topic], indent=indent)

            # Any %Previous's?
            if topic in deparsed["that"]:
                self._write_triggers(fh, deparsed["that"][topic], indent=indent)

            if tagged:
                fh.write("< topic\n\n")

        return True

    def _copy_trigger(self, trig, data, previous=None):
        """Make copies of all data below a trigger.

        :param str trig: The trigger key.
        :param dict data: The data under that trigger.
        :param previous: The ``%Previous`` for the trigger.
        """
        # Copied data.
        dest = {}

        if previous:
            dest["previous"] = previous

        if "redirect" in data and data["redirect"]:
            # @Redirect
            dest["redirect"] = data["redirect"]

        if "condition" in data and len(data["condition"].keys()):
            # *Condition
            dest["condition"] = []
            for i in sorted(data["condition"].keys()):
                dest["condition"].append(data["condition"][i])

        if "reply" in data and len(data["reply"].keys()):
            # -Reply
            dest["reply"] = []
            for i in sorted(data["reply"].keys()):
                dest["reply"].append(data["reply"][i])

        return dest

    def _write_triggers(self, fh, triggers, indent=""):
        """Write triggers to a file handle.

        :param fh: The file handle.
        :param dict triggers: The triggers to write to the file.
        :param str indent: The indentation (spaces) to prefix each line with.
        """

        for trig in sorted(triggers.keys()):
            fh.write(indent + "+ " + self._write_wrapped(trig, indent=indent) + "\n")
            d = triggers[trig]

            if "previous" in d:
                fh.write(indent + "% " + self._write_wrapped(d["previous"], indent=indent) + "\n")

            if "condition" in d:
                for cond in d["condition"]:
                    fh.write(indent + "* " + self._write_wrapped(cond, indent=indent) + "\n")

            if "redirect" in d:
                fh.write(indent + "@ " + self._write_wrapped(d["redirect"], indent=indent) + "\n")

            if "reply" in d:
                for reply in d["reply"]:
                    fh.write(indent + "- " + self._write_wrapped(reply, indent=indent) + "\n")

            fh.write("\n")

    def _write_wrapped(self, line, sep=" ", indent="", width=78):
        """Word-wrap a line of RiveScript code for being written to a file.

        :param str line: The original line of text to word-wrap.
        :param str sep: The word separator.
        :param str indent: The indentation to use (as a set of spaces).
        :param int width: The character width to constrain each line to.

        :return str: The reformatted line(s)."""

        words = line.split(sep)
        lines = []
        line  = ""
        buf   = []

        while len(words):
            buf.append(words.pop(0))
            line = sep.join(buf)
            if len(line) > width:
                # Need to word wrap!
                words.insert(0, buf.pop())  # Undo
                lines.append(sep.join(buf))
                buf = []
                line = ""

        # Straggler?
        if line:
            lines.append(line)

        # Returned output
        result = lines.pop(0)
        if len(lines):
            eol = ""
            if sep == " ":
                eol = "\s"
            for item in lines:
                result += eol + "\n" + indent + "^ " + item

        return result

    ############################################################################
    # Sorting Methods                                                          #
    ############################################################################

    def sort_replies(self, thats=False):
        """Sort the loaded triggers in memory.

        After you have finished loading your RiveScript code, call this method
        to populate the various internal sort buffers. This is absolutely
        necessary for reply matching to work efficiently!
        """
        # (Re)initialize the sort cache.
        self._sorted["topics"] = {}
        self._sorted["thats"]  = {}
        self._say("Sorting triggers...")

        # Loop through all the topics.
        for topic in self._topics.keys():
            self._say("Analyzing topic " + topic)

            # Collect a list of all the triggers we're going to worry about.
            # If this topic inherits another topic, we need to recursively add
            # those to the list as well.
            alltrig = inherit_utils.get_topic_triggers(self, topic, False)

            # Sort them.
            self._sorted["topics"][topic] = sorting.sort_trigger_set(alltrig, True, self._say)

            # Get all of the %Previous triggers for this topic.
            that_triggers = inherit_utils.get_topic_triggers(self, topic, True)

            # And sort them, too.
            self._sorted["thats"][topic] = sorting.sort_trigger_set(that_triggers, False, self._say)

        # And sort the substitution lists.
        if not "lists" in self._sorted:
            self._sorted["lists"] = {}
        self._sorted["lists"]["sub"] = sorting.sort_list(self._sub.keys())
        self._sorted["lists"]["person"] = sorting.sort_list(self._person.keys())

    ############################################################################
    # Public Configuration Methods                                             #
    ############################################################################

    def set_handler(self, language, obj):
        """Define a custom language handler for RiveScript objects.

        Pass in a ``None`` value for the object to delete an existing handler (for
        example, to prevent Python code from being able to be run by default).

        Look in the ``eg`` folder of the rivescript-python distribution for
        an example script that sets up a JavaScript language handler.

        :param str language: The lowercased name of the programming language.
            Examples: python, javascript, perl
        :param class obj: An instance of an implementation class object.
            It should provide the following interface::

                class MyObjectHandler:
                    def __init__(self):
                        pass
                    def load(self, name, code):
                        # name = the name of the object from the RiveScript code
                        # code = the source code of the object
                    def call(self, rs, name, fields):
                        # rs     = the current RiveScript interpreter object
                        # name   = the name of the object being called
                        # fields = array of arguments passed to the object
                        return reply
        """

        # Allow them to delete a handler too.
        if obj is None:
            if language in self._handlers:
                del self._handlers[language]
        else:
            self._handlers[language] = obj

    def set_subroutine(self, name, code):
        """Define a Python object from your program.

        This is equivalent to having an object defined in the RiveScript code,
        except your Python code is defining it instead.

        :param str name: The name of the object macro.
        :param def code: A Python function with a method signature of
            ``(rs, args)``

        This method is only available if there is a Python handler set up
        (which there is by default, unless you've called
        ``set_handler("python", None)``).
        """

        # Do we have a Python handler?
        if 'python' in self._handlers:
            self._handlers['python']._objects[name] = code
            self._objlangs[name] = 'python'
        else:
            self._warn("Can't set_subroutine: no Python object handler!")

    def set_global(self, name, value):
        """Set a global variable.

        Equivalent to ``! global`` in RiveScript code.

        :param str name: The name of the variable to set.
        :param str value: The value of the variable.
            Set this to ``None`` to delete the variable.
        """
        if value is None:
            # Unset the variable.
            if name in self._global:
                del self._global[name]
        self._global[name] = value

    def get_global(self, name):
        """Retrieve the current value of a global variable.

        :param str name: The name of the variable to get.
        :return str: The value of the variable or ``"undefined"``.
        """
        return self._global.get(name, "undefined")

    def set_variable(self, name, value):
        """Set a bot variable.

        Equivalent to ``! var`` in RiveScript code.

        :param str name: The name of the variable to set.
        :param str value: The value of the variable.
            Set this to ``None`` to delete the variable.
        """
        if value is None:
            # Unset the variable.
            if name in self._var:
                del self._var[name]
        self._var[name] = value

    def get_variable(self, name):
        """Retrieve the current value of a bot variable.

        :param str name: The name of the variable to get.
        :return str: The value of the variable or ``"undefined"``.
        """
        return self._var.get(name, "undefined")

    def set_substitution(self, what, rep):
        """Set a substitution.

        Equivalent to ``! sub`` in RiveScript code.

        :param str what: The original text to replace.
        :param str rep: The text to replace it with.
            Set this to ``None`` to delete the substitution.
        """
        if rep is None:
            # Unset the variable.
            if what in self._subs:
                del self._subs[what]
        self._subs[what] = rep

    def set_person(self, what, rep):
        """Set a person substitution.

        Equivalent to ``! person`` in RiveScript code.

        :param str what: The original text to replace.
        :param str rep: The text to replace it with.
            Set this to ``None`` to delete the substitution.
        """
        if rep is None:
            # Unset the variable.
            if what in self._person:
                del self._person[what]
        self._person[what] = rep

    def set_uservar(self, user, name, value):
        """Set a variable for a user.

        This is like the ``<set>`` tag in RiveScript code.

        :param str user: The user ID to set a variable for.
        :param str name: The name of the variable to set.
        :param str value: The value to set there.
        """
        self._session.set(user, {name: value})

    def set_uservars(self, user, data=None):
        """Set many variables for a user, or set many variables for many users.

        This function can be called in two ways::

            # Set a dict of variables for a single user.
            rs.set_uservars(username, vars)

            # Set a nested dict of variables for many users.
            rs.set_uservars(many_vars)

        In the first syntax, ``vars`` is a simple dict of key/value string
        pairs. In the second syntax, ``many_vars`` is a structure like this::

            {
                "username1": {
                    "key": "value",
                },
                "username2": {
                    "key": "value",
                },
            }

        This way you can export *all* user variables via ``get_uservars()``
        and then re-import them all at once, instead of setting them once per
        user.

        :param optional str user: The user ID to set many variables for.
            Skip this parameter to set many variables for many users instead.
        :param dict data: The dictionary of key/value pairs for user variables,
            or else a dict of dicts mapping usernames to key/value pairs.

        This may raise a ``TypeError`` exception if you pass it invalid data
        types. Note that only the standard ``dict`` type is accepted, but not
        variants like ``OrderedDict``, so if you have a dict-like type you
        should cast it to ``dict`` first.
        """

        # Check the parameters to see how we're being used.
        if type(user) is dict and data is None:
            # Setting many variables for many users.
            for uid, uservars in user.items():
                if type(uservars) is not dict:
                    raise TypeError(
                        "In set_uservars(many_vars) syntax, the many_vars dict "
                        "must be in the format of `many_vars['username'] = "
                        "dict(key=value)`, but the contents of many_vars['{}']"
                        " is not a dict.".format(uid)
                    )

                self._session.set(uid, uservars)

        elif type(user) in [text_type, str] and type(data) is dict:
            # Setting variables for a single user.
            self._session.set(user, data)

        else:
            raise TypeError(
                "set_uservars() may only be called with types ({str}, dict) or "
                "(dict<{str}, dict>) but you called it with types ({a}, {b})"
                .format(
                    str="unicode" if sys.version_info[0] < 3 else "str",
                    a=type(user),
                    b=type(data),
                ),
            )

    def get_uservar(self, user, name):
        """Get a variable about a user.

        :param str user: The user ID to look up a variable for.
        :param str name: The name of the variable to get.

        :return: The user variable, or ``None`` or ``"undefined"``:

            * If the user has no data at all, this returns ``None``.
            * If the user doesn't have this variable set, this returns the
              string ``"undefined"``.
            * Otherwise this returns the string value of the variable.
        """
        if name == '__lastmatch__':  # Treat var `__lastmatch__` since it can't receive "undefined" value
            return self.last_match(user)
        else:
            return self._session.get(user, name)

    def get_uservars(self, user=None):
        """Get all variables about a user (or all users).

        :param optional str user: The user ID to retrieve all variables for.
            If not passed, this function will return all data for all users.

        :return dict: All the user variables.

            * If a ``user`` was passed, this is a ``dict`` of key/value pairs
              of that user's variables. If the user doesn't exist in memory,
              this returns ``None``.
            * Otherwise, this returns a ``dict`` of key/value pairs that map
              user IDs to their variables (a ``dict`` of ``dict``).
        """

        if user is None:
            # All the users!
            return self._session.get_all()
        else:
            # Just this one!
            return self._session.get_any(user)

    def clear_uservars(self, user=None):
        """Delete all variables about a user (or all users).

        :param str user: The user ID to clear variables for, or else clear all
            variables for all users if not provided.
        """

        if user is None:
            # All the users!
            self._session.reset_all()
        else:
            # Just this one.
            self._session.reset(user)

    def freeze_uservars(self, user):
        """Freeze the variable state for a user.

        This will clone and preserve a user's entire variable state, so that it
        can be restored later with ``thaw_uservars()``.

        :param str user: The user ID to freeze variables for.
        """
        self._session.freeze(user)

    def thaw_uservars(self, user, action="thaw"):
        """Thaw a user's frozen variables.

        :param str action: The action to perform when thawing the variables:

            * ``discard``: Don't restore the user's variables, just delete the
              frozen copy.
            * ``keep``: Keep the frozen copy after restoring the variables.
            * ``thaw``: Restore the variables, then delete the frozen copy
              (this is the default).
        """
        self._session.thaw(user, action)

    def last_match(self, user):
        """Get the last trigger matched for the user.

        :param str user: The user ID to get the last matched trigger for.
        :return str: The raw trigger text (tags and all) of the trigger that
            the user most recently matched. If there was no match to their
            last message, this returns ``None`` instead.
        """
        return self._session.get(user, "__lastmatch__", None) # Get directly to `get` function

    def trigger_info(self, trigger=None, dump=False):
        """Get information about a trigger.

        Pass in a raw trigger to find out what file name and line number it
        appeared at. This is useful for e.g. tracking down the location of the
        trigger last matched by the user via ``last_match()``. Returns a list
        of matching triggers, containing their topics, filenames and line
        numbers. Returns ``None`` if there weren't any matches found.

        The keys in the trigger info is as follows:

        * ``category``: Either 'topic' (for normal) or 'thats'
          (for %Previous triggers)
        * ``topic``: The topic name
        * ``trigger``: The raw trigger text
        * ``filename``: The filename the trigger was found in.
        * ``lineno``: The line number the trigger was found on.

        Pass in a true value for ``dump``, and the entire syntax tracking
        tree is returned.

        :param str trigger: The raw trigger text to look up.
        :param bool dump: Whether to dump the entire syntax tracking tree.

        :return: A list of matching triggers or ``None`` if no matches.
        """
        if dump:
            return self._syntax

        response = None

        # Search the syntax tree for the trigger.
        for category in self._syntax:
            for topic in self._syntax[category]:
                if trigger in self._syntax[category][topic]:
                    # We got a match!
                    if response is None:
                        response = list()
                    fname, lineno = self._syntax[category][topic][trigger]['trigger']
                    response.append(dict(
                        category=category,
                        topic=topic,
                        trigger=trigger,
                        filename=fname,
                        line=lineno,
                    ))

        return response

    def current_user(self):
        """Retrieve the user ID of the current user talking to your bot.

        This is mostly useful inside of a Python object macro to get the user
        ID of the person who caused the object macro to be invoked (i.e. to
        set a variable for that user from within the object).

        This will return ``None`` if used outside of the context of getting a
        reply (the value is unset at the end of the ``reply()`` method).
        """
        if self._brain._current_user is None:
            # They're doing it wrong.
            self._warn("current_user() is meant to be used from within a Python object macro!")
        return self._brain._current_user

    ############################################################################
    # Reply Fetching Methods                                                   #
    ############################################################################

    def reply(self, user, msg, errors_as_replies=True):
        """Fetch a reply from the RiveScript brain.

        Arguments:
            user (str): A unique user ID for the person requesting a reply.
                This could be e.g. a screen name or nickname. It's used internally
                to store user variables (including topic and history), so if your
                bot has multiple users each one should have a unique ID.
            msg (str): The user's message. This is allowed to contain
                punctuation and such, but any extraneous data such as HTML tags
                should be removed in advance.
            errors_as_replies (bool): When errors are encountered (such as a
                deep recursion error, no reply matched, etc.) this will make the
                reply be a text representation of the error message. If you set
                this to ``False``, errors will instead raise an exception, such as
                a ``DeepRecursionError`` or ``NoReplyError``. By default, no
                exceptions are raised and errors are set in the reply instead.

        Returns:
            str: The reply output.
        """
        return self._brain.reply(user, msg, errors_as_replies)

    def _precompile_substitution(self, kind, pattern):
        """Pre-compile the regexp for a substitution pattern.

        This will speed up the substitutions that happen at the beginning of
        the reply fetching process. With the default brain, this took the
        time for _substitute down from 0.08s to 0.02s

        :param str kind: One of ``sub``, ``person``.
        :param str pattern: The substitution pattern.
        """
        if pattern not in self._regexc[kind]:
            qm = re.escape(pattern)
            self._regexc[kind][pattern] = {
                "qm": qm,
                "sub1": re.compile(r'^' + qm + r'$'),
                "sub2": re.compile(r'^' + qm + r'(\W+)'),
                "sub3": re.compile(r'(\W+)' + qm + r'(\W+)'),
                "sub4": re.compile(r'(\W+)' + qm + r'$'),
            }

    def _precompile_regexp(self, trigger):
        """Precompile the regex for most triggers.

        If the trigger is non-atomic, and doesn't include dynamic tags like
        ``<bot>``, ``<get>``, ``<input>/<reply>`` or arrays, it can be
        precompiled and save time when matching.

        :param str trigger: The trigger text to attempt to precompile.
        """
        if utils.is_atomic(trigger):
            return  # Don't need a regexp for atomic triggers.

        # Check for dynamic tags.
        for tag in ["@", "<bot", "<get", "<input", "<reply"]:
            if tag in trigger:
                return  # Can't precompile this trigger.

        self._regexc["trigger"][trigger] = self._brain.reply_regexp(None, trigger)

    ############################################################################
    # Miscellaneous Private Methods                                            #
    ############################################################################

    def _dump(self):
        """For debugging, dump the entire data structure."""
        pp = pprint.PrettyPrinter(indent=4)

        print("=== Variables ===")
        print("-- Globals --")
        pp.pprint(self._global)
        print("-- Bot vars --")
        pp.pprint(self._var)
        print("-- Substitutions --")
        pp.pprint(self._sub)
        print("-- Person Substitutions --")
        pp.pprint(self._person)
        print("-- Arrays --")
        pp.pprint(self._array)

        print("=== Topic Structure ===")
        pp.pprint(self._topics)
        print("=== %Previous Structure ===")
        pp.pprint(self._thats)

        print("=== Includes ===")
        pp.pprint(self._includes)

        print("=== Inherits ===")
        pp.pprint(self._lineage)

        print("=== Sort Buffer ===")
        pp.pprint(self._sorted)

        print("=== Syntax Tree ===")
        pp.pprint(self._syntax)

################################################################################
# Interactive Mode                                                             #
################################################################################

if __name__ == "__main__":
    from interactive import interactive_mode
    interactive_mode()

# vim:expandtab
