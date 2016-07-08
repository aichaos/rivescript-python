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

from __future__ import unicode_literals
from six import text_type
import sys
import os
import re
import string
import random
import pprint
import copy
import codecs

from . import __version__
from . import python
from .regexp import RE
from .exceptions import (
    RS_ERR_MATCH, RS_ERR_REPLY, RS_ERR_DEEP_RECURSION, RS_ERR_OBJECT,
    RS_ERR_OBJECT_HANDLER, RS_ERR_OBJECT_MISSING, RiveScriptError,
    NoMatchError, NoReplyError, ObjectError, DeepRecursionError,
    NoDefaultRandomTopicError, RepliesNotSortedError
)

# These constants come from the exceptions submodule but should be exportable
# from this one. Pyflakes gives warnings about them not being used, so...
_ = RS_ERR_MATCH
_ = RS_ERR_REPLY
_ = RS_ERR_DEEP_RECURSION

# Version of RiveScript we support.
rs_version = 2.0

class RiveScript(object):
    """A RiveScript interpreter for Python 2 and 3.

    :param bool debug: Set to True to enable verbose logging.

    :param bool strict: Enable strict mode.
        Strict mode causes RiveScript syntax errors to be fatal.
        This option is ``True`` by default.

    :param str log: Specify a log file to write debug output to.
        This can redirect debug lines to a file instead of ``STDOUT``.

    :param int depth: Specify the recursion depth limit.
        This is how many times RiveScript will recursively follow redirects
        before giving up with a ``DeepRecursionError`` exception.
        The default is ``50``.

    :param bool utf8: Enable UTF-8 mode.
        The default is ``False``.
    """

    # Concatenation mode characters.
    _concat_modes = dict(
        none="",
        space=" ",
        newline="\n",
    )

    ############################################################################
    # Initialization and Utility Methods                                       #
    ############################################################################

    def __init__(self, debug=False, strict=True, depth=50, log="", utf8=False):
        """Initialize a new RiveScript interpreter."""

        ###
        # User configurable fields.
        ###

        # Debugging
        self._debug = debug   # Debug mode
        self._log   = log     # Debug log file

        # Unicode stuff
        self._utf8               = utf8  # UTF-8 mode
        self.unicode_punctuation = re.compile(r'[.,!?;:]')

        # Misc.
        self._strict = strict  # Strict mode
        self._depth  = depth   # Recursion depth limit

        ###
        # Internal fields.
        ###
        self._gvars    = {}      # 'global' variables
        self._bvars    = {}      # 'bot' variables
        self._subs     = {}      # 'sub' variables
        self._person   = {}      # 'person' variables
        self._arrays   = {}      # 'array' variables
        self._users    = {}      # 'user' variables
        self._freeze   = {}      # frozen 'user' variables
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
            "subs":    {},
            "person":  {},
        }

        # "Current request" variables.
        self._current_user = None  # The current user ID.

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
        if self._debug:
            print("[RS] {}".format(message))
        if self._log:
            # Log it to the file.
            fh = open(self._log, 'a')
            fh.write("[RS] " + message + "\n")
            fh.close()

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

        for item in os.listdir(directory):
            for extension in ext:
                if item.lower().endswith(extension):
                    # Load this file.
                    self.load_file(os.path.join(directory, item))
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
        self._say("Parsing code")

        # Track temporary variables.
        topic   = 'random'  # Default topic=random
        lineno  = 0         # Line numbers for syntax tracking
        comment = False     # In a multi-line comment
        inobj   = False     # In an object
        objname = ''        # The name of the object we're in
        objlang = ''        # The programming language of the object
        objbuf  = []        # Object contents buffer
        ontrig  = ''        # The current trigger
        repcnt  = 0         # Reply counter
        concnt  = 0         # Condition counter
        isThat  = ''        # Is a %Previous trigger

        # Local (file scoped) parser options.
        local_options = dict(
            concat="none",  # Concat mode for ^Continue command
        )

        # Read each line.
        for lp, line in enumerate(code):
            lineno += 1

            self._say("Line: " + line + " (topic: " + topic + ") incomment: " + str(inobj))
            if len(line.strip()) == 0:  # Skip blank lines
                continue

            # In an object?
            if inobj:
                if re.match(RE.objend, line):
                    # End the object.
                    if len(objname):
                        # Call the object's handler.
                        if objlang in self._handlers:
                            self._objlangs[objname] = objlang
                            self._handlers[objlang].load(objname, objbuf)
                        else:
                            self._warn("Object creation failed: no handler for " + objlang, fname, lineno)
                    objname = ''
                    objlang = ''
                    objbuf  = []
                    inobj   = False
                else:
                    objbuf.append(line)
                continue

            line = line.strip()  # Trim excess space. We do it down here so we
                                 # don't mess up python objects!

            # Look for comments.
            if line[:2] == '//':  # A single-line comment.
                continue
            elif line[0] == '#':
                self._warn("Using the # symbol for comments is deprecated", fname, lineno)
            elif line[:2] == '/*':  # Start of a multi-line comment.
                if '*/' not in line:  # Cancel if the end is here too.
                    comment = True
                continue
            elif '*/' in line:
                comment = False
                continue
            if comment:
                continue

            # Separate the command from the data.
            if len(line) < 2:
                self._warn("Weird single-character line '" + line + "' found.", fname, lineno)
                continue
            cmd = line[0]
            line = line[1:].strip()

            # Ignore inline comments if there's a space before and after
            # the // symbols.
            if " // " in line:
                line = line.split(" // ")[0].strip()

            # Run a syntax check on this line.
            syntax_error = self.check_syntax(cmd, line)
            if syntax_error:
                # There was a syntax error! Are we enforcing strict mode?
                syntax_error = "Syntax error in " + fname + " line " + str(lineno) + ": " \
                    + syntax_error + " (near: " + cmd + " " + line + ")"
                if self._strict:
                    raise Exception(syntax_error)
                else:
                    self._warn(syntax_error)
                    return  # Don't try to continue

            # Reset the %Previous state if this is a new +Trigger.
            if cmd == '+':
                isThat = ''

            # Do a lookahead for ^Continue and %Previous commands.
            for i in range(lp + 1, len(code)):
                lookahead = code[i].strip()
                if len(lookahead) < 2:
                    continue
                lookCmd = lookahead[0]
                lookahead = lookahead[1:].strip()

                # Only continue if the lookahead line has any data.
                if len(lookahead) != 0:
                    # The lookahead command has to be either a % or a ^.
                    if lookCmd != '^' and lookCmd != '%':
                        break

                    # If the current command is a +, see if the following is
                    # a %.
                    if cmd == '+':
                        if lookCmd == '%':
                            isThat = lookahead
                            break
                        else:
                            isThat = ''

                    # If the current command is a ! and the next command(s) are
                    # ^, we'll tack each extension on as a line break (which is
                    # useful information for arrays).
                    if cmd == '!':
                        if lookCmd == '^':
                            line += "<crlf>" + lookahead
                        continue

                    # If the current command is not a ^ and the line after is
                    # not a %, but the line after IS a ^, then tack it on to the
                    # end of the current line.
                    if cmd != '^' and lookCmd != '%':
                        if lookCmd == '^':
                            line += self._concat_modes.get(
                                local_options["concat"], ""
                            ) + lookahead
                        else:
                            break

            self._say("Command: " + cmd + "; line: " + line)

            # Handle the types of RiveScript commands.
            if cmd == '!':
                # ! DEFINE
                halves = re.split(RE.equals, line, 2)
                left = re.split(RE.ws, halves[0].strip(), 2)
                value, type, var = '', '', ''
                if len(halves) == 2:
                    value = halves[1].strip()
                if len(left) >= 1:
                    type = left[0].strip()
                    if len(left) >= 2:
                        var = ' '.join(left[1:]).strip()

                # Remove 'fake' line breaks unless this is an array.
                if type != 'array':
                    value = re.sub(RE.crlf, '', value)

                # Handle version numbers.
                if type == 'version':
                    # Verify we support it.
                    try:
                        if float(value) > rs_version:
                            self._warn("Unsupported RiveScript version. We only support " + rs_version, fname, lineno)
                            return
                    except:
                        self._warn("Error parsing RiveScript version number: not a number", fname, lineno)
                    continue

                # All other types of defines require a variable and value name.
                if len(var) == 0:
                    self._warn("Undefined variable name", fname, lineno)
                    continue
                elif len(value) == 0:
                    self._warn("Undefined variable value", fname, lineno)
                    continue

                # Handle the rest of the types.
                if type == 'local':
                    # Local file-scoped parser options.
                    self._say("\tSet parser option " + var + " = " + value)
                    local_options[var] = value
                elif type == 'global':
                    # 'Global' variables
                    self._say("\tSet global " + var + " = " + value)

                    if value == '<undef>':
                        try:
                            del(self._gvars[var])
                        except:
                            self._warn("Failed to delete missing global variable", fname, lineno)
                    else:
                        self._gvars[var] = value

                    # Handle flipping debug and depth vars.
                    if var == 'debug':
                        if value.lower() == 'true':
                            value = True
                        else:
                            value = False
                        self._debug = value
                    elif var == 'depth':
                        try:
                            self._depth = int(value)
                        except:
                            self._warn("Failed to set 'depth' because the value isn't a number!", fname, lineno)
                    elif var == 'strict':
                        if value.lower() == 'true':
                            self._strict = True
                        else:
                            self._strict = False
                elif type == 'var':
                    # Bot variables
                    self._say("\tSet bot variable " + var + " = " + value)

                    if value == '<undef>':
                        try:
                            del(self._bvars[var])
                        except:
                            self._warn("Failed to delete missing bot variable", fname, lineno)
                    else:
                        self._bvars[var] = value
                elif type == 'array':
                    # Arrays
                    self._say("\tArray " + var + " = " + value)

                    if value == '<undef>':
                        try:
                            del(self._arrays[var])
                        except:
                            self._warn("Failed to delete missing array", fname, lineno)
                        continue

                    # Did this have multiple parts?
                    parts = value.split("<crlf>")

                    # Process each line of array data.
                    fields = []
                    for val in parts:
                        if '|' in val:
                            fields.extend(val.split('|'))
                        else:
                            fields.extend(re.split(RE.ws, val))

                    # Convert any remaining '\s' escape codes into spaces.
                    for f in fields:
                        f = f.replace('\s', ' ')

                    self._arrays[var] = fields
                elif type == 'sub':
                    # Substitutions
                    self._say("\tSubstitution " + var + " => " + value)

                    if value == '<undef>':
                        try:
                            del(self._subs[var])
                        except:
                            self._warn("Failed to delete missing substitution", fname, lineno)
                    else:
                        self._subs[var] = value

                    # Precompile the regexp.
                    self._precompile_substitution("subs", var)
                elif type == 'person':
                    # Person Substitutions
                    self._say("\tPerson Substitution " + var + " => " + value)

                    if value == '<undef>':
                        try:
                            del(self._person[var])
                        except:
                            self._warn("Failed to delete missing person substitution", fname, lineno)
                    else:
                        self._person[var] = value

                    # Precompile the regexp.
                    self._precompile_substitution("person", var)
                else:
                    self._warn("Unknown definition type '" + type + "'", fname, lineno)
            elif cmd == '>':
                # > LABEL
                temp = re.split(RE.ws, line)
                type   = temp[0]
                name   = ''
                fields = []
                if len(temp) >= 2:
                    name = temp[1]
                if len(temp) >= 3:
                    fields = temp[2:]

                # Handle the label types.
                if type == 'begin':
                    # The BEGIN block.
                    self._say("\tFound the BEGIN block.")
                    type = 'topic'
                    name = '__begin__'
                if type == 'topic':
                    # Starting a new topic.
                    self._say("\tSet topic to " + name)
                    ontrig = ''
                    topic  = name

                    # Does this topic include or inherit another one?
                    mode = ''  # or 'inherits' or 'includes'
                    if len(fields) >= 2:
                        for field in fields:
                            if field == 'includes':
                                mode = 'includes'
                            elif field == 'inherits':
                                mode = 'inherits'
                            elif mode != '':
                                # This topic is either inherited or included.
                                if mode == 'includes':
                                    if name not in self._includes:
                                        self._includes[name] = {}
                                    self._includes[name][field] = 1
                                else:
                                    if name not in self._lineage:
                                        self._lineage[name] = {}
                                    self._lineage[name][field] = 1
                elif type == 'object':
                    # If a field was provided, it should be the programming
                    # language.
                    lang = None
                    if len(fields) > 0:
                        lang = fields[0].lower()

                    # Only try to parse a language we support.
                    ontrig = ''
                    if lang is None:
                        self._warn("Trying to parse unknown programming language", fname, lineno)
                        lang = 'python'  # Assume it's Python.

                    # See if we have a defined handler for this language.
                    if lang in self._handlers:
                        # We have a handler, so start loading the code.
                        objname = name
                        objlang = lang
                        objbuf  = []
                        inobj   = True
                    else:
                        # We don't have a handler, just ignore it.
                        objname = ''
                        objlang = ''
                        objbuf  = []
                        inobj   = True
                else:
                    self._warn("Unknown label type '" + type + "'", fname, lineno)
            elif cmd == '<':
                # < LABEL
                type = line

                if type == 'begin' or type == 'topic':
                    self._say("\tEnd topic label.")
                    topic = 'random'
                elif type == 'object':
                    self._say("\tEnd object label.")
                    inobj = False
            elif cmd == '+':
                # + TRIGGER
                self._say("\tTrigger pattern: " + line)
                if len(isThat):
                    self._initTT('thats', topic, isThat, line)
                    self._initTT('syntax', topic, line, 'thats')
                    self._syntax['thats'][topic][line]['trigger'] = (fname, lineno)
                else:
                    self._initTT('topics', topic, line)
                    self._initTT('syntax', topic, line, 'topic')
                    self._syntax['topic'][topic][line]['trigger'] = (fname, lineno)
                ontrig = line
                repcnt = 0
                concnt = 0

                # Pre-compile the trigger's regexp if possible.
                self._precompile_regexp(ontrig)
            elif cmd == '-':
                # - REPLY
                if ontrig == '':
                    self._warn("Response found before trigger", fname, lineno)
                    continue
                self._say("\tResponse: " + line)
                if len(isThat):
                    self._thats[topic][isThat][ontrig]['reply'][repcnt] = line
                    self._syntax['thats'][topic][ontrig]['reply'][repcnt] = (fname, lineno)
                else:
                    self._topics[topic][ontrig]['reply'][repcnt] = line
                    self._syntax['topic'][topic][ontrig]['reply'][repcnt] = (fname, lineno)
                repcnt += 1
            elif cmd == '%':
                # % PREVIOUS
                pass  # This was handled above.
            elif cmd == '^':
                # ^ CONTINUE
                pass  # This was handled above.
            elif cmd == '@':
                # @ REDIRECT
                self._say("\tRedirect response to " + line)
                if len(isThat):
                    self._thats[topic][isThat][ontrig]['redirect'] = line
                    self._syntax['thats'][topic][ontrig]['redirect'] = (fname, lineno)
                else:
                    self._topics[topic][ontrig]['redirect'] = line
                    self._syntax['topic'][topic][ontrig]['redirect'] = (fname, lineno)
            elif cmd == '*':
                # * CONDITION
                self._say("\tAdding condition: " + line)
                if len(isThat):
                    self._thats[topic][isThat][ontrig]['condition'][concnt] = line
                    self._syntax['thats'][topic][ontrig]['condition'][concnt] = (fname, lineno)
                else:
                    self._topics[topic][ontrig]['condition'][concnt] = line
                    self._syntax['topic'][topic][ontrig]['condition'][concnt] = (fname, lineno)
                concnt += 1
            else:
                self._warn("Unrecognized command \"" + cmd + "\"", fname, lineno)
                continue

    def check_syntax(self, cmd, line):
        """Syntax check a line of RiveScript code.

        :param str cmd: The command symbol for the line of code, such as one
            of ``+``, ``-``, ``*``, ``>``, etc.
        :param str line: The remainder of the line of code, such as the text of
            a trigger or reply.

        :return: A string syntax error message or ``None`` if no errors.
        """

        # Run syntax checks based on the type of command.
        if cmd == '!':
            # ! Definition
            #   - Must be formatted like this:
            #     ! type name = value
            #     OR
            #     ! type = value
            match = re.match(RE.def_syntax, line)
            if not match:
                return "Invalid format for !Definition line: must be '! type name = value' OR '! type = value'"
        elif cmd == '>':
            # > Label
            #   - The "begin" label must have only one argument ("begin")
            #   - "topic" labels must be lowercased but can inherit other topics (a-z0-9_\s)
            #   - "object" labels must follow the same rules as "topic", but don't need to be lowercase
            parts = re.split(" ", line, 2)
            if parts[0] == "begin" and len(parts) > 1:
                return "The 'begin' label takes no additional arguments, should be verbatim '> begin'"
            elif parts[0] == "topic":
                match = re.match(RE.name_syntax, line)
                if match:
                    return "Topics should be lowercased and contain only numbers and letters"
            elif parts[0] == "object":
                match = re.match(RE.name_syntax, line)
                if match:
                    return "Objects can only contain numbers and letters"
        elif cmd == '+' or cmd == '%' or cmd == '@':
            # + Trigger, % Previous, @ Redirect
            #   This one is strict. The triggers are to be run through the regexp engine,
            #   therefore it should be acceptable for the regexp engine.
            #   - Entirely lowercase
            #   - No symbols except: ( | ) [ ] * _ # @ { } < > =
            #   - All brackets should be matched
            parens = 0  # Open parenthesis
            square = 0  # Open square brackets
            curly  = 0  # Open curly brackets
            angle  = 0  # Open angled brackets

            # Count brackets.
            for char in line:
                if char == '(':
                    parens += 1
                elif char == ')':
                    parens -= 1
                elif char == '[':
                    square += 1
                elif char == ']':
                    square -= 1
                elif char == '{':
                    curly += 1
                elif char == '}':
                    curly -= 1
                elif char == '<':
                    angle += 1
                elif char == '>':
                    angle -= 1

            # Any mismatches?
            if parens != 0:
                return "Unmatched parenthesis brackets"
            elif square != 0:
                return "Unmatched square brackets"
            elif curly != 0:
                return "Unmatched curly brackets"
            elif angle != 0:
                return "Unmatched angle brackets"

            # In UTF-8 mode, most symbols are allowed.
            if self._utf8:
                match = re.match(RE.utf8_trig, line)
                if match:
                    return "Triggers can't contain uppercase letters, backslashes or dots in UTF-8 mode."
            else:
                match = re.match(RE.trig_syntax, line)
                if match:
                    return "Triggers may only contain lowercase letters, numbers, and these symbols: ( | ) [ ] * _ # @ { } < > ="
        elif cmd == '-' or cmd == '^' or cmd == '/':
            # - Trigger, ^ Continue, / Comment
            # These commands take verbatim arguments, so their syntax is loose.
            pass
        elif cmd == '*':
            # * Condition
            #   Syntax for a conditional is as follows:
            #   * value symbol value => response
            match = re.match(RE.cond_syntax, line)
            if not match:
                return "Invalid format for !Condition: should be like '* value symbol value => response'"

        return None

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
        result["begin"]["var"]    = self._bvars.copy()
        result["begin"]["sub"]    = self._subs.copy()
        result["begin"]["person"] = self._person.copy()
        result["begin"]["array"]  = self._arrays.copy()
        result["begin"]["global"].update(self._gvars.copy())

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

    def _initTT(self, toplevel, topic, trigger, what=''):
        """Initialize a Topic Tree data structure.

        :param str toplevel: One of ``topics``, ``thats`` or ``syntax``
        :param str topic: The topic name.
        :param str trigger: The trigger text.
        :param str what: Trigger text or ``thats`` depending on context.
        """
        if toplevel == 'topics':
            if topic not in self._topics:
                self._topics[topic] = {}
            if trigger not in self._topics[topic]:
                self._topics[topic][trigger]              = {}
                self._topics[topic][trigger]['reply']     = {}
                self._topics[topic][trigger]['condition'] = {}
                self._topics[topic][trigger]['redirect']  = None
        elif toplevel == 'thats':
            if topic not in self._thats:
                self._thats[topic] = {}
            if trigger not in self._thats[topic]:
                self._thats[topic][trigger] = {}
            if what not in self._thats[topic][trigger]:
                self._thats[topic][trigger][what] = {}
                self._thats[topic][trigger][what]['reply']     = {}
                self._thats[topic][trigger][what]['condition'] = {}
                self._thats[topic][trigger][what]['redirect']  = {}
        elif toplevel == 'syntax':
            if what not in self._syntax:
                self._syntax[what] = {}
            if topic not in self._syntax[what]:
                self._syntax[what][topic] = {}
            if trigger not in self._syntax[what][topic]:
                self._syntax[what][topic][trigger]              = {}
                self._syntax[what][topic][trigger]['reply']     = {}
                self._syntax[what][topic][trigger]['condition'] = {}
                self._syntax[what][topic][trigger]['redirect']  = {}

    ############################################################################
    # Sorting Methods                                                          #
    ############################################################################

    def sort_replies(self, thats=False):
        """Sort the loaded triggers.

        Don't send any parameters when you call this function.

        :param private bool thats: You shouldn't use this parameter, it's used
            internally. Sorting is done in two passes: first the normal triggers
            are sorted, and then triggers that have a ``%Previous`` command.
            The ``thats`` argument is used to sort the latter, and this function
            automatically does so, so don't worry about this argument.
        """
        # This method can sort both triggers and that's.
        triglvl = None
        sortlvl = None
        if thats:
            triglvl = self._thats
            sortlvl = 'thats'
        else:
            triglvl = self._topics
            sortlvl = 'topics'

        # (Re)Initialize the sort cache.
        self._sorted[sortlvl] = {}

        self._say("Sorting triggers...")

        # Loop through all the topics.
        for topic in triglvl:
            self._say("Analyzing topic " + topic)

            # Collect a list of all the triggers we're going to need to worry
            # about. If this topic inherits another topic, we need to
            # recursively add those to the list.
            alltrig = self._topic_triggers(topic, triglvl)

            # Keep in mind here that there is a difference between 'includes'
            # and 'inherits' -- topics that inherit other topics are able to
            # OVERRIDE triggers that appear in the inherited topic. This means
            # that if the top topic has a trigger of simply '*', then *NO*
            # triggers are capable of matching in ANY inherited topic, because
            # even though * has the lowest sorting priority, it has an automatic
            # priority over all inherited topics.
            #
            # The _topic_triggers method takes this into account. All topics
            # that inherit other topics will have their triggers prefixed with
            # a fictional {inherits} tag, which would start at {inherits=0} and
            # increment if the topic tree has other inheriting topics. So we can
            # use this tag to make sure topics that inherit things will have
            # their triggers always be on top of the stack, from inherits=0 to
            # inherits=n.

            # Sort these triggers.
            running = self._sort_trigger_set(alltrig)

            # Save this topic's sorted list.
            if sortlvl not in self._sorted:
                self._sorted[sortlvl] = {}
            self._sorted[sortlvl][topic] = running

        # And do it all again for %Previous!
        if not thats:
            # This will sort the %Previous lines to best match the bot's last reply.
            self.sort_replies(True)

            # If any of those %Previous's had more than one +trigger for them,
            # this will sort all those +triggers to pair back the best human
            # interaction.
            self._sort_that_triggers()

            # Also sort both kinds of substitutions.
            self._sort_list('subs', self._subs)
            self._sort_list('person', self._person)

    def _sort_that_triggers(self):
        """Make a sorted list of triggers that correspond to %Previous groups."""
        self._say("Sorting reverse triggers for %Previous groups...")

        if "that_trig" not in self._sorted:
            self._sorted["that_trig"] = {}

        for topic in self._thats:
            if topic not in self._sorted["that_trig"]:
                self._sorted["that_trig"][topic] = {}

            for bottrig in self._thats[topic]:
                if bottrig not in self._sorted["that_trig"][topic]:
                    self._sorted["that_trig"][topic][bottrig] = []
                triggers = self._sort_trigger_set(self._thats[topic][bottrig].keys())
                self._sorted["that_trig"][topic][bottrig] = triggers

    def _sort_trigger_set(self, triggers):
        """Sort a group of triggers in optimal sorting order.

        The optimal sorting order is, briefly:
        * Atomic triggers (containing nothing but plain words and alternation
          groups) are on top, with triggers containing the most words coming
          first. Triggers with equal word counts are sorted by length, and then
          alphabetically if they have the same length.
        * Triggers containing optionals are sorted next, by word count like
          atomic triggers.
        * Triggers containing wildcards are next, with ``_`` (alphabetic)
          wildcards on top, then ``#`` (numeric) and finally ``*``.
        * At the bottom of the sorted list are triggers consisting of only a
          single wildcard, in the order: ``_``, ``#``, ``*``.

        Triggers that have ``{weight}`` tags are grouped together by weight
        value and sorted amongst themselves. Higher weighted groups are then
        ordered before lower weighted groups regardless of the normal sorting
        algorithm.

        Triggers that come from topics which inherit other topics are also
        sorted with higher priority than triggers from the inherited topics.
        """

        # Create a priority map.
        prior = {
            0: []  # Default priority=0
        }

        for trig in triggers:
            match, weight = re.search(RE.weight, trig), 0
            if match:
                weight = int(match.group(1))
            if weight not in prior:
                prior[weight] = []

            prior[weight].append(trig)

        # Keep a running list of sorted triggers for this topic.
        running = []

        # Sort them by priority.
        for p in sorted(prior.keys(), reverse=True):
            self._say("\tSorting triggers with priority " + str(p))

            # So, some of these triggers may include {inherits} tags, if they
            # came form a topic which inherits another topic. Lower inherits
            # values mean higher priority on the stack.
            inherits = -1          # -1 means no {inherits} tag
            highest_inherits = -1  # highest inheritance number seen

            # Loop through and categorize these triggers.
            track = {
                inherits: self._init_sort_track()
            }

            for trig in prior[p]:
                self._say("\t\tLooking at trigger: " + trig)

                # See if it has an inherits tag.
                match = re.search(RE.inherit, trig)
                if match:
                    inherits = int(match.group(1))
                    if inherits > highest_inherits:
                        highest_inherits = inherits
                    self._say("\t\t\tTrigger belongs to a topic which inherits other topics: level=" + str(inherits))
                    trig = re.sub(RE.inherit, "", trig)
                else:
                    inherits = -1

                # If this is the first time we've seen this inheritance level,
                # initialize its track structure.
                if inherits not in track:
                    track[inherits] = self._init_sort_track()

                # Start inspecting the trigger's contents.
                if '_' in trig:
                    # Alphabetic wildcard included.
                    cnt = self._word_count(trig)
                    self._say("\t\t\tHas a _ wildcard with " + str(cnt) + " words.")
                    if cnt > 1:
                        if cnt not in track[inherits]['alpha']:
                            track[inherits]['alpha'][cnt] = []
                        track[inherits]['alpha'][cnt].append(trig)
                    else:
                        track[inherits]['under'].append(trig)
                elif '#' in trig:
                    # Numeric wildcard included.
                    cnt = self._word_count(trig)
                    self._say("\t\t\tHas a # wildcard with " + str(cnt) + " words.")
                    if cnt > 1:
                        if cnt not in track[inherits]['number']:
                            track[inherits]['number'][cnt] = []
                        track[inherits]['number'][cnt].append(trig)
                    else:
                        track[inherits]['pound'].append(trig)
                elif '*' in trig:
                    # Wildcard included.
                    cnt = self._word_count(trig)
                    self._say("\t\t\tHas a * wildcard with " + str(cnt) + " words.")
                    if cnt > 1:
                        if cnt not in track[inherits]['wild']:
                            track[inherits]['wild'][cnt] = []
                        track[inherits]['wild'][cnt].append(trig)
                    else:
                        track[inherits]['star'].append(trig)
                elif '[' in trig:
                    # Optionals included.
                    cnt = self._word_count(trig)
                    self._say("\t\t\tHas optionals and " + str(cnt) + " words.")
                    if cnt not in track[inherits]['option']:
                        track[inherits]['option'][cnt] = []
                    track[inherits]['option'][cnt].append(trig)
                else:
                    # Totally atomic.
                    cnt = self._word_count(trig)
                    self._say("\t\t\tTotally atomic and " + str(cnt) + " words.")
                    if cnt not in track[inherits]['atomic']:
                        track[inherits]['atomic'][cnt] = []
                    track[inherits]['atomic'][cnt].append(trig)

            # Move the no-{inherits} triggers to the bottom of the stack.
            track[highest_inherits + 1] = track[-1]
            del(track[-1])

            # Add this group to the sort list.
            for ip in sorted(track.keys()):
                self._say("ip=" + str(ip))
                for kind in ['atomic', 'option', 'alpha', 'number', 'wild']:
                    for wordcnt in sorted(track[ip][kind], reverse=True):
                        # Triggers with a matching word count should be sorted
                        # by length, descending.
                        running.extend(sorted(track[ip][kind][wordcnt], key=len, reverse=True))
                running.extend(sorted(track[ip]['under'], key=len, reverse=True))
                running.extend(sorted(track[ip]['pound'], key=len, reverse=True))
                running.extend(sorted(track[ip]['star'], key=len, reverse=True))
        return running

    def _sort_list(self, name, items):
        """Sort a simple list by number of words and length."""

        def by_length(word1, word2):
            return len(word2) - len(word1)

        # Initialize the list sort buffer.
        if "lists" not in self._sorted:
            self._sorted["lists"] = {}
        self._sorted["lists"][name] = []

        # Track by number of words.
        track = {}

        # Loop through each item.
        for item in items:
            # Count the words.
            cword = self._word_count(item, all=True)
            if cword not in track:
                track[cword] = []
            track[cword].append(item)

        # Sort them.
        output = []
        for count in sorted(track.keys(), reverse=True):
            sort = sorted(track[count], key=len, reverse=True)
            output.extend(sort)

        self._sorted["lists"][name] = output

    def _init_sort_track(self):
        """Returns a new dict for keeping track of triggers for sorting."""
        return {
            'atomic': {},  # Sort by number of whole words
            'option': {},  # Sort optionals by number of words
            'alpha':  {},  # Sort alpha wildcards by no. of words
            'number': {},  # Sort number wildcards by no. of words
            'wild':   {},  # Sort wildcards by no. of words
            'pound':  [],  # Triggers of just #
            'under':  [],  # Triggers of just _
            'star':   []   # Triggers of just *
        }


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
            if name in self._gvars:
                del self._gvars[name]
        self._gvars[name] = value

    def get_global(self, name):
        """Retrieve the current value of a global variable.

        :param str name: The name of the variable to get.
        :return str: The value of the variable or ``"undefined"``.
        """
        return self._gvars.get(name, "undefined")

    def set_variable(self, name, value):
        """Set a bot variable.

        Equivalent to ``! var`` in RiveScript code.

        :param str name: The name of the variable to set.
        :param str value: The value of the variable.
            Set this to ``None`` to delete the variable.
        """
        if value is None:
            # Unset the variable.
            if name in self._bvars:
                del self._bvars[name]
        self._bvars[name] = value

    def get_variable(self, name):
        """Retrieve the current value of a bot variable.

        :param str name: The name of the variable to get.
        :return str: The value of the variable or ``"undefined"``.
        """
        return self._bvars.get(name, "undefined")

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

        if user not in self._users:
            self._users[user] = {"topic": "random"}

        self._users[user][name] = value

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

                if not uid in self._users:
                    self._users[uid] = dict(topic="random")

                for key, value in uservars.items():
                    self._users[uid][key] = value

        elif type(user) in [text_type, str] and type(data) is dict:
            # Setting variables for a single user.
            if not user in self._users:
                self._users[user] = dict(topic="random")

            for key, value in data.items():
                self._users[user][key] = value

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

        if user in self._users:
            if name in self._users[user]:
                return self._users[user][name]
            else:
                return "undefined"
        else:
            return None

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
            return self._users
        elif user in self._users:
            # Just this one!
            return self._users[user]
        else:
            # No info.
            return None

    def clear_uservars(self, user=None):
        """Delete all variables about a user (or all users).

        :param str user: The user ID to clear variables for, or else clear all
            variables for all users if not provided.
        """

        if user is None:
            # All the users!
            self._users = {}
        elif user in self._users:
            # Just this one.
            self._users[user] = {}

    def freeze_uservars(self, user):
        """Freeze the variable state for a user.

        This will clone and preserve a user's entire variable state, so that it
        can be restored later with ``thaw_uservars()``.

        :param str user: The user ID to freeze variables for.
        """

        if user in self._users:
            # Clone the user's data.
            self._freeze[user] = copy.deepcopy(self._users[user])
        else:
            self._warn("Can't freeze vars for user " + user + ": not found!")

    def thaw_uservars(self, user, action="thaw"):
        """Thaw a user's frozen variables.

        :param str action: The action to perform when thawing the variables:

            * ``discard``: Don't restore the user's variables, just delete the
              frozen copy.
            * ``keep``: Keep the frozen copy after restoring the variables.
            * ``thaw``: Restore the variables, then delete the frozen copy
              (this is the default).
        """

        if user in self._freeze:
            # What are we doing?
            if action == "thaw":
                # Thawing them out.
                self.clear_uservars(user)
                self._users[user] = copy.deepcopy(self._freeze[user])
                del self._freeze[user]
            elif action == "discard":
                # Just discard the frozen copy.
                del self._freeze[user]
            elif action == "keep":
                # Keep the frozen copy afterward.
                self.clear_uservars(user)
                self._users[user] = copy.deepcopy(self._freeze[user])
            else:
                self._warn("Unsupported thaw action")
        else:
            self._warn("Can't thaw vars for user " + user + ": not found!")

    def last_match(self, user):
        """Get the last trigger matched for the user.

        :param str user: The user ID to get the last matched trigger for.
        :return str: The raw trigger text (tags and all) of the trigger that
            the user most recently matched. If there was no match to their
            last message, this returns ``None`` instead.
        """
        return self.get_uservar(user, "__lastmatch__")

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
        if self._current_user is None:
            # They're doing it wrong.
            self._warn("current_user() is meant to be used from within a Python object macro!")
        return self._current_user

    ############################################################################
    # Reply Fetching Methods                                                   #
    ############################################################################

    def reply(self, user, msg, errors_as_replies=True):
        """Fetch a reply from the RiveScript brain.

        :param str user: A unique user ID for the person requesting a reply.
            This could be e.g. a screen name or nickname. It's used internally
            to store user variables (including topic and history), so if your
            bot has multiple users each one should have a unique ID.
        :param str msg: The user's message. This is allowed to contain
            punctuation and such, but any extraneous data such as HTML tags
            should be removed in advance.
        :param bool errors_as_replies: When errors are encountered (such as a
            deep recursion error, no reply matched, etc.) this will make the
            reply be a text representation of the error message. If you set
            this to ``False``, errors will instead raise an exception, such as
            a ``DeepRecursionError`` or ``NoReplyError``. By default, no
            exceptions are raised and errors are set in the reply instead.

        :return str: The reply output.
        """
        self._say("Get reply to [" + user + "] " + msg)

        # Store the current user in case an object macro needs it.
        self._current_user = user

        # Format their message.
        msg = self._format_message(msg)

        reply = ''

        # If the BEGIN block exists, consult it first.
        if "__begin__" in self._topics:
            begin = self._getreply(user, 'request', context='begin', ignore_object_errors=errors_as_replies)

            # Okay to continue?
            if '{ok}' in begin:
                try:
                    reply = self._getreply(user, msg, ignore_object_errors=errors_as_replies)
                except RiveScriptError as e:
                    if not errors_as_replies:
                        raise
                    reply = e.error_message
                begin = begin.replace('{ok}', reply)

            reply = begin

            # Run more tag substitutions.
            reply = self._process_tags(user, msg, reply, ignore_object_errors=errors_as_replies)
        else:
            # Just continue then.
            try:
                reply = self._getreply(user, msg, ignore_object_errors=errors_as_replies)
            except RiveScriptError as e:
                if not errors_as_replies:
                    raise
                reply = e.error_message

        # Save their reply history.
        oldInput = self._users[user]['__history__']['input'][:8]
        self._users[user]['__history__']['input'] = [msg]
        self._users[user]['__history__']['input'].extend(oldInput)
        oldReply = self._users[user]['__history__']['reply'][:8]
        self._users[user]['__history__']['reply'] = [reply]
        self._users[user]['__history__']['reply'].extend(oldReply)

        # Unset the current user.
        self._current_user = None

        return reply

    def _format_message(self, msg, botreply=False):
        """Format a user's message for safe processing.

        This runs substitutions on the message and strips out any remaining
        symbols (depending on UTF-8 mode).

        :param str msg: The user's message.
        :param bool botreply: Whether this formatting is being done for the
            bot's last reply (e.g. in a ``%Previous`` command).

        :return str: The formatted message.
        """

        # Make sure the string is Unicode for Python 2.
        if sys.version_info[0] < 3 and isinstance(msg, str):
            msg = msg.decode()

        # Lowercase it.
        msg = msg.lower()

        # Run substitutions on it.
        msg = self._substitute(msg, "subs")

        # In UTF-8 mode, only strip metacharacters and HTML brackets
        # (to protect from obvious XSS attacks).
        if self._utf8:
            msg = re.sub(RE.utf8_meta, '', msg)
            msg = re.sub(self.unicode_punctuation, '', msg)

            # For the bot's reply, also strip common punctuation.
            if botreply:
                msg = re.sub(RE.utf8_punct, '', msg)
        else:
            # For everything else, strip all non-alphanumerics.
            msg = self._strip_nasties(msg)

        return msg

    def _getreply(self, user, msg, context='normal', step=0, ignore_object_errors=True):
        """The internal reply getter function.

        DO NOT CALL THIS YOURSELF.

        :param str user: The user ID as passed to ``reply()``.
        :param str msg: The formatted user message.
        :param str context: The reply context, one of ``begin`` or ``normal``.
        :param int step: The recursion depth counter.
        :param bool ignore_object_errors: Whether to ignore errors from within
            Python object macros and not raise an ``ObjectError`` exception.

        :return str: The reply output.
        """
        # Needed to sort replies?
        if 'topics' not in self._sorted:
            raise RepliesNotSortedError("You must call sort_replies() once you are done loading RiveScript documents")

        # Initialize the user's profile?
        if user not in self._users:
            self._users[user] = {'topic': 'random'}

        # Collect data on the user.
        topic     = self._users[user]['topic']
        stars     = []
        thatstars = []  # For %Previous's.
        reply     = ''

        # Avoid letting them fall into a missing topic.
        if topic not in self._topics:
            self._warn("User " + user + " was in an empty topic named '" + topic + "'")
            topic = self._users[user]['topic'] = 'random'

        # Avoid deep recursion.
        if step > self._depth:
            raise DeepRecursionError

        # Are we in the BEGIN statement?
        if context == 'begin':
            topic = '__begin__'

        # Initialize this user's history.
        if '__history__' not in self._users[user]:
            self._users[user]['__history__'] = {
                'input': [
                    'undefined', 'undefined', 'undefined', 'undefined',
                    'undefined', 'undefined', 'undefined', 'undefined',
                    'undefined'
                ],
                'reply': [
                    'undefined', 'undefined', 'undefined', 'undefined',
                    'undefined', 'undefined', 'undefined', 'undefined',
                    'undefined'
                ]
            }

        # More topic sanity checking.
        if topic not in self._topics:
            # This was handled before, which would mean topic=random and
            # it doesn't exist. Serious issue!
            raise NoDefaultRandomTopicError("no default topic 'random' was found")

        # Create a pointer for the matched data when we find it.
        matched        = None
        matchedTrigger = None
        foundMatch     = False

        # See if there were any %Previous's in this topic, or any topic related
        # to it. This should only be done the first time -- not during a
        # recursive redirection. This is because in a redirection, "lastreply"
        # is still gonna be the same as it was the first time, causing an
        # infinite loop!
        if step == 0:
            allTopics = [topic]
            if topic in self._includes or topic in self._lineage:
                # Get all the topics!
                allTopics = self._get_topic_tree(topic)

            # Scan them all!
            for top in allTopics:
                self._say("Checking topic " + top + " for any %Previous's.")
                if top in self._sorted["thats"]:
                    self._say("There is a %Previous in this topic!")

                    # Do we have history yet?
                    lastReply = self._users[user]["__history__"]["reply"][0]

                    # Format the bot's last reply the same way as the human's.
                    lastReply = self._format_message(lastReply, botreply=True)

                    self._say("lastReply: " + lastReply)

                    # See if it's a match.
                    for trig in self._sorted["thats"][top]:
                        botside = self._reply_regexp(user, trig)
                        self._say("Try to match lastReply (" + lastReply + ") to " + trig)

                        # Match??
                        match = re.match(botside, lastReply)
                        if match:
                            # Huzzah! See if OUR message is right too.
                            self._say("Bot side matched!")
                            thatstars = match.groups()
                            for subtrig in self._sorted["that_trig"][top][trig]:
                                humanside = self._reply_regexp(user, subtrig)
                                self._say("Now try to match " + msg + " to " + subtrig)

                                match = re.match(humanside, msg)
                                if match:
                                    self._say("Found a match!")
                                    matched = self._thats[top][trig][subtrig]
                                    matchedTrigger = subtrig
                                    foundMatch = True

                                    # Get the stars!
                                    stars = match.groups()
                                    break

                        # Break if we found a match.
                        if foundMatch:
                            break
                # Break if we found a match.
                if foundMatch:
                    break

        # Search their topic for a match to their trigger.
        if not foundMatch:
            for trig in self._sorted["topics"][topic]:
                # Process the triggers.
                regexp = self._reply_regexp(user, trig)
                self._say("Try to match %r against %r (%r)" % (msg, trig, regexp.pattern))

                # Python's regular expression engine is slow. Try a verbatim
                # match if this is an atomic trigger.
                isAtomic = self._is_atomic(trig)
                isMatch = False
                if isAtomic:
                    # Only look for exact matches, no sense running atomic triggers
                    # through the regexp engine.
                    if msg == trig:
                        isMatch = True
                else:
                    # Non-atomic triggers always need the regexp.
                    match = re.match(regexp, msg)
                    if match:
                        # The regexp matched!
                        isMatch = True

                        # Collect the stars.
                        stars = match.groups()

                if isMatch:
                    self._say("Found a match!")

                    # We found a match, but what if the trigger we've matched
                    # doesn't belong to our topic? Find it!
                    if trig not in self._topics[topic]:
                        # We have to find it.
                        matched = self._find_trigger_by_inheritance(topic, trig)
                    else:
                        # We do have it!
                        matched = self._topics[topic][trig]

                    foundMatch = True
                    matchedTrigger = trig
                    break

        # Store what trigger they matched on. If their matched trigger is None,
        # this will be too, which is great.
        self._users[user]["__lastmatch__"] = matchedTrigger

        if matched:
            for nil in [1]:
                # See if there are any hard redirects.
                if matched["redirect"]:
                    self._say("Redirecting us to " + matched["redirect"])
                    redirect = self._process_tags(user, msg, matched["redirect"], stars, thatstars, step,
                                                  ignore_object_errors)
                    self._say("Pretend user said: " + redirect)
                    reply = self._getreply(user, redirect, step=(step + 1), ignore_object_errors=ignore_object_errors)
                    break

                # Check the conditionals.
                for con in sorted(matched["condition"]):
                    halves = re.split(RE.cond_split, matched["condition"][con])
                    if halves and len(halves) == 2:
                        condition = re.match(RE.cond_parse, halves[0])
                        if condition:
                            left     = condition.group(1)
                            eq       = condition.group(2)
                            right    = condition.group(3)
                            potreply = halves[1]
                            self._say("Left: " + left + "; eq: " + eq + "; right: " + right + " => " + potreply)

                            # Process tags all around.
                            left  = self._process_tags(user, msg, left, stars, thatstars, step, ignore_object_errors)
                            right = self._process_tags(user, msg, right, stars, thatstars, step, ignore_object_errors)

                            # Defaults?
                            if len(left) == 0:
                                left = 'undefined'
                            if len(right) == 0:
                                right = 'undefined'

                            self._say("Check if " + left + " " + eq + " " + right)

                            # Validate it.
                            passed = False
                            if eq == 'eq' or eq == '==':
                                if left == right:
                                    passed = True
                            elif eq == 'ne' or eq == '!=' or eq == '<>':
                                if left != right:
                                    passed = True
                            else:
                                # Gasp, dealing with numbers here...
                                try:
                                    left, right = int(left), int(right)
                                    if eq == '<':
                                        if left < right:
                                            passed = True
                                    elif eq == '<=':
                                        if left <= right:
                                            passed = True
                                    elif eq == '>':
                                        if left > right:
                                            passed = True
                                    elif eq == '>=':
                                        if left >= right:
                                            passed = True
                                except:
                                    self._warn("Failed to evaluate numeric condition!")

                            # How truthful?
                            if passed:
                                reply = potreply
                                break

                # Have our reply yet?
                if len(reply) > 0:
                    break

                # Process weights in the replies.
                bucket = []
                for rep in sorted(matched["reply"]):
                    text = matched["reply"][rep]
                    weight = 1
                    match  = re.match(RE.weight, text)
                    if match:
                        weight = int(match.group(1))
                        if weight <= 0:
                            self._warn("Can't have a weight <= 0!")
                            weight = 1
                    for i in range(0, weight):
                        bucket.append(text)

                # Get a random reply.
                reply = random.choice(bucket)
                break

        # Still no reply?
        if not foundMatch:
            raise NoMatchError
        elif len(reply) == 0:
            raise NoReplyError

        self._say("Reply: " + reply)

        # Process tags for the BEGIN block.
        if context == "begin":
            # BEGIN blocks can only set topics and uservars. The rest happen
            # later!
            reTopic = re.findall(RE.topic_tag, reply)
            for match in reTopic:
                self._say("Setting user's topic to " + match)
                self._users[user]["topic"] = match
                reply = reply.replace('{{topic={match}}}'.format(match=match), '')

            reSet = re.findall(RE.set_tag, reply)
            for match in reSet:
                self._say("Set uservar " + str(match[0]) + "=" + str(match[1]))
                self._users[user][match[0]] = match[1]
                reply = reply.replace('<set {key}={value}>'.format(key=match[0], value=match[1]), '')
        else:
            # Process more tags if not in BEGIN.
            reply = self._process_tags(user, msg, reply, stars, thatstars, step, ignore_object_errors)

        return reply

    def _substitute(self, msg, kind):
        """Run a kind of substitution on a message.

        :param str msg: The message to run substitutions against.
        :param str kind: The kind of substitution to run,
            one of ``subs`` or ``person``.
        """

        # Safety checking.
        if 'lists' not in self._sorted:
            raise RepliesNotSortedError("You must call sort_replies() once you are done loading RiveScript documents")
        if kind not in self._sorted["lists"]:
            raise RepliesNotSortedError("You must call sort_replies() once you are done loading RiveScript documents")

        # Get the substitution map.
        subs = None
        if kind == 'subs':
            subs = self._subs
        else:
            subs = self._person

        # Make placeholders each time we substitute something.
        ph = []
        i  = 0

        for pattern in self._sorted["lists"][kind]:
            result = subs[pattern]

            # Make a placeholder.
            ph.append(result)
            placeholder = "\x00%d\x00" % i
            i += 1

            cache = self._regexc[kind][pattern]
            msg = re.sub(cache["sub1"], placeholder, msg)
            msg = re.sub(cache["sub2"], placeholder + r'\1', msg)
            msg = re.sub(cache["sub3"], r'\1' + placeholder + r'\2', msg)
            msg = re.sub(cache["sub4"], r'\1' + placeholder, msg)

        placeholders = re.findall(RE.placeholder, msg)
        for match in placeholders:
            i = int(match)
            result = ph[i]
            msg = msg.replace('\x00' + match + '\x00', result)

        # Strip & return.
        return msg.strip()

    def _precompile_substitution(self, kind, pattern):
        """Pre-compile the regexp for a substitution pattern.

        This will speed up the substitutions that happen at the beginning of
        the reply fetching process. With the default brain, this took the
        time for _substitute down from 0.08s to 0.02s

        :param str kind: One of ``sub``, ``person``.
        :param str pattern: The substitution pattern.
        """
        if pattern not in self._regexc[kind]:
            qm = self._quotemeta(pattern)
            self._regexc[kind][pattern] = {
                "qm": qm,
                "sub1": re.compile(r'^' + qm + r'$'),
                "sub2": re.compile(r'^' + qm + r'(\W+)'),
                "sub3": re.compile(r'(\W+)' + qm + r'(\W+)'),
                "sub4": re.compile(r'(\W+)' + qm + r'$'),
            }

    def _do_expand_array(self, array_name, depth=0):
        """Do recurrent array expansion, returning a set of keywords.

        Exception is thrown when there are cyclical dependencies between
        arrays or if the ``@array`` name references an undefined array.

        :param str array_name: The name of the array to expand.
        :param int depth: The recursion depth counter.

        :return set: The final set of array entries.
        """
        if depth > self._depth:
            raise Exception("deep recursion detected")
        if not array_name in self._arrays:
            raise Exception("array '%s' not defined" % (array_name))
        ret = list(self._arrays[array_name])
        for array in self._arrays[array_name]:
            if array.startswith('@'):
                ret.remove(array)
                expanded = self._do_expand_array(array[1:], depth+1)
                ret.extend(expanded)

        return set(ret)

    def _expand_array(self, array_name):
        """Expand variables and return a set of keywords.

        :param str array_name: The name of the array to expand.

        :return list: The final array contents.

        Warning is issued when exceptions occur."""
        ret = self._arrays[array_name] if array_name in self._arrays else []
        try:
            ret = self._do_expand_array(array_name)
        except Exception as e:
            self._warn("Error expanding array '%s': %s" % (array_name, str(e)))
        return ret


    def _reply_regexp(self, user, regexp):
        """Prepares a trigger for the regular expression engine.

        :param str user: The user ID invoking a reply.
        :param str regexp: The original trigger text to be turned into a regexp.

        :return regexp: The final regexp object."""

        if regexp in self._regexc["trigger"]:
            # Already compiled this one!
            return self._regexc["trigger"][regexp]

        # If the trigger is simply '*' then the * there needs to become (.*?)
        # to match the blank string too.
        regexp = re.sub(RE.zero_star, r'<zerowidthstar>', regexp)

        # Simple replacements.
        regexp = regexp.replace('*', '(.+?)')   # Convert * into (.+?)
        regexp = regexp.replace('#', '(\d+?)')  # Convert # into (\d+?)
        regexp = regexp.replace('_', '(\w+?)')  # Convert _ into (\w+?)
        regexp = re.sub(r'\{weight=\d+\}', '', regexp)  # Remove {weight} tags
        regexp = regexp.replace('<zerowidthstar>', r'(.*?)')

        # Optionals.
        optionals = re.findall(RE.optionals, regexp)
        for match in optionals:
            parts = match.split("|")
            new = []
            for p in parts:
                p = r'(?:\\s|\\b)+{}(?:\\s|\\b)+'.format(p)
                new.append(p)

            # If this optional had a star or anything in it, make it
            # non-matching.
            pipes = '|'.join(new)
            pipes = re.sub(self._quotemeta(r'(.+?)'), '(?:.+?)', pipes)
            pipes = re.sub(self._quotemeta(r'(\d+?)'), '(?:\d+?)', pipes)
            pipes = re.sub(self._quotemeta(r'([A-Za-z]+?)'), '(?:[A-Za-z]+?)', pipes)

            regexp = re.sub(r'\s*\[' + self._quotemeta(match) + '\]\s*',
                '(?:' + pipes + r'|(?:\\s|\\b))', regexp)

        # _ wildcards can't match numbers!
        regexp = re.sub(RE.literal_w, r'[A-Za-z]', regexp)

        # Filter in arrays.
        arrays = re.findall(RE.array, regexp)
        for array in arrays:
            rep = ''
            if array in self._arrays:
                rep = r'(?:' + '|'.join(self._expand_array(array)) + ')'
            regexp = re.sub(r'\@' + self._quotemeta(array) + r'\b', rep, regexp)

        # Filter in bot variables.
        bvars = re.findall(RE.bot_tag, regexp)
        for var in bvars:
            rep = ''
            if var in self._bvars:
                rep = self._strip_nasties(self._bvars[var])
            regexp = regexp.replace('<bot {var}>'.format(var=var), rep)

        # Filter in user variables.
        uvars = re.findall(RE.get_tag, regexp)
        for var in uvars:
            rep = ''
            if var in self._users[user]:
                rep = self._strip_nasties(self._users[user][var])
            regexp = regexp.replace('<get {var}>'.format(var=var), rep)

        # Filter in <input> and <reply> tags. This is a slow process, so only
        # do it if we have to!
        if '<input' in regexp or '<reply' in regexp:
            for type in ['input', 'reply']:
                tags = re.findall(r'<' + type + r'([0-9])>', regexp)
                for index in tags:
                    rep = self._format_message(self._users[user]['__history__'][type][int(index) - 1])
                    regexp = regexp.replace('<{type}{index}>'.format(type=type, index=index), rep)
                regexp = regexp.replace('<{type}>'.format(type=type),
                                        self._format_message(self._users[user]['__history__'][type][0]))
                # TODO: the Perl version doesn't do just <input>/<reply> in trigs!

        return re.compile(r'^' + regexp + r'$')

    def _precompile_regexp(self, trigger):
        """Precompile the regex for most triggers.

        If the trigger is non-atomic, and doesn't include dynamic tags like
        ``<bot>``, ``<get>``, ``<input>/<reply>`` or arrays, it can be
        precompiled and save time when matching.

        :param str trigger: The trigger text to attempt to precompile.
        """
        if self._is_atomic(trigger):
            return  # Don't need a regexp for atomic triggers.

        # Check for dynamic tags.
        for tag in ["@", "<bot", "<get", "<input", "<reply"]:
            if tag in trigger:
                return  # Can't precompile this trigger.

        self._regexc["trigger"][trigger] = self._reply_regexp(None, trigger)

    def _process_tags(self, user, msg, reply, st=[], bst=[], depth=0, ignore_object_errors=True):
        """Post process tags in a message.

        :param str user: The user ID.
        :param str msg: The user's formatted message.
        :param str reply: The raw RiveScript reply for the message.
        :param []str st: The array of ``<star>`` matches from the trigger.
        :param []str bst: The array of ``<botstar>`` matches from a
            ``%Previous`` command.
        :param int depth: The recursion depth counter.
        :param bool ignore_object_errors: Whether to ignore errors in Python
            object macros instead of raising an ``ObjectError`` exception.

        :return str: The final reply after tags have been processed.
        """
        stars = ['']
        stars.extend(st)
        botstars = ['']
        botstars.extend(bst)
        if len(stars) == 1:
            stars.append("undefined")
        if len(botstars) == 1:
            botstars.append("undefined")

        # Tag shortcuts.
        reply = reply.replace('<person>', '{person}<star>{/person}')
        reply = reply.replace('<@>', '{@<star>}')
        reply = reply.replace('<formal>', '{formal}<star>{/formal}')
        reply = reply.replace('<sentence>', '{sentence}<star>{/sentence}')
        reply = reply.replace('<uppercase>', '{uppercase}<star>{/uppercase}')
        reply = reply.replace('<lowercase>', '{lowercase}<star>{/lowercase}')

        # Weight and <star> tags.
        reply = re.sub(RE.weight, '', reply)  # Leftover {weight}s
        if len(stars) > 0:
            reply = reply.replace('<star>', stars[1])
            reStars = re.findall(RE.star_tags, reply)
            for match in reStars:
                if int(match) < len(stars):
                    reply = reply.replace('<star{match}>'.format(match=match), stars[int(match)])
        if len(botstars) > 0:
            reply = reply.replace('<botstar>', botstars[1])
            reStars = re.findall(RE.botstars, reply)
            for match in reStars:
                if int(match) < len(botstars):
                    reply = reply.replace('<botstar{match}>'.format(match=match), botstars[int(match)])

        # <input> and <reply>
        reply = reply.replace('<input>', self._users[user]['__history__']['input'][0])
        reply = reply.replace('<reply>', self._users[user]['__history__']['reply'][0])
        reInput = re.findall(RE.input_tags, reply)
        for match in reInput:
            reply = reply.replace('<input{match}>'.format(match=match),
                                  self._users[user]['__history__']['input'][int(match) - 1])
        reReply = re.findall(RE.reply_tags, reply)
        for match in reReply:
            reply = reply.replace('<reply{match}>'.format(match=match),
                                  self._users[user]['__history__']['reply'][int(match) - 1])

        # <id> and escape codes.
        reply = reply.replace('<id>', user)
        reply = reply.replace('\\s', ' ')
        reply = reply.replace('\\n', "\n")
        reply = reply.replace('\\#', '#')

        # Random bits.
        reRandom = re.findall(RE.random_tags, reply)
        for match in reRandom:
            output = ''
            if '|' in match:
                output = random.choice(match.split('|'))
            else:
                output = random.choice(match.split(' '))
            reply = reply.replace('{{random}}{match}{{/random}}'.format(match=match), output)

        # Person Substitutions and String Formatting.
        for item in ['person', 'formal', 'sentence', 'uppercase',  'lowercase']:
            matcher = re.findall(r'\{' + item + r'\}(.+?)\{/' + item + r'\}', reply)
            for match in matcher:
                output = None
                if item == 'person':
                    # Person substitutions.
                    output = self._substitute(match, "person")
                else:
                    output = self._string_format(match, item)
                reply = reply.replace('{{{item}}}{match}{{/{item}}}'.format(item=item, match=match), output)

        # Handle all variable-related tags with an iterative regex approach,
        # to allow for nesting of tags in arbitrary ways (think <set a=<get b>>)
        # Dummy out the <call> tags first, because we don't handle them right
        # here.
        reply = reply.replace("<call>", "{__call__}")
        reply = reply.replace("</call>", "{/__call__}")
        while True:
            # This regex will match a <tag> which contains no other tag inside
            # it, i.e. in the case of <set a=<get b>> it will match <get b> but
            # not the <set> tag, on the first pass. The second pass will get the
            # <set> tag, and so on.
            match = re.search(RE.tag_search, reply)
            if not match: break  # No remaining tags!

            match = match.group(1)
            parts  = match.split(" ", 1)
            tag    = parts[0].lower()
            data   = parts[1] if len(parts) > 1 else ""
            insert = ""  # Result of the tag evaluation

            # Handle the tags.
            if tag == "bot" or tag == "env":
                # <bot> and <env> tags are similar.
                target = self._bvars if tag == "bot" else self._gvars
                if "=" in data:
                    # Setting a bot/env variable.
                    parts = data.split("=")
                    self._say("Set " + tag + " variable " + text_type(parts[0]) + "=" + text_type(parts[1]))
                    target[parts[0]] = parts[1]
                else:
                    # Getting a bot/env variable.
                    insert = target.get(data, "undefined")
            elif tag == "set":
                # <set> user vars.
                parts = data.split("=")
                self._say("Set uservar " + text_type(parts[0]) + "=" + text_type(parts[1]))
                self._users[user][parts[0]] = parts[1]
            elif tag in ["add", "sub", "mult", "div"]:
                # Math operator tags.
                parts = data.split("=")
                var   = parts[0]
                value = parts[1]

                # Sanity check the value.
                try:
                    value = int(value)
                    if var not in self._users[user]:
                        # Initialize it.
                        self._users[user][var] = 0
                except:
                    insert = "[ERR: Math can't '{}' non-numeric value '{}']".format(tag, value)

                # Attempt the operation.
                try:
                    orig = int(self._users[user][var])
                    new  = 0
                    if tag == "add":
                        new = orig + value
                    elif tag == "sub":
                        new = orig - value
                    elif tag == "mult":
                        new = orig * value
                    elif tag == "div":
                        new = orig / value
                    self._users[user][var] = new
                except:
                    insert = "[ERR: Math couldn't '{}' to value '{}']".format(tag, self._users[user][var])
            elif tag == "get":
                insert = self._users[user].get(data, "undefined")
            else:
                # Unrecognized tag.
                insert = "\x00{}\x01".format(match)

            reply = reply.replace("<{}>".format(match), insert)

        # Restore unrecognized tags.
        reply = reply.replace("\x00", "<").replace("\x01", ">")

        # Streaming code. DEPRECATED!
        if '{!' in reply:
            self._warn("Use of the {!...} tag is deprecated and not supported here.")

        # Topic setter.
        reTopic = re.findall(RE.topic_tag, reply)
        for match in reTopic:
            self._say("Setting user's topic to " + match)
            self._users[user]["topic"] = match
            reply = reply.replace('{{topic={match}}}'.format(match=match), '')

        # Inline redirecter.
        reRedir = re.findall(RE.redir_tag, reply)
        for match in reRedir:
            self._say("Redirect to " + match)
            at = match.strip()
            subreply = self._getreply(user, at, step=(depth + 1))
            reply = reply.replace('{{@{match}}}'.format(match=match), subreply)

        # Object caller.
        reply = reply.replace("{__call__}", "<call>")
        reply = reply.replace("{/__call__}", "</call>")
        reCall = re.findall(r'<call>(.+?)</call>', reply)
        for match in reCall:
            parts  = re.split(RE.ws, match)
            output = ''
            obj    = parts[0]
            args   = []
            if len(parts) > 1:
                args = parts[1:]

            # Do we know this object?
            if obj in self._objlangs:
                # We do, but do we have a handler for that language?
                lang = self._objlangs[obj]
                if lang in self._handlers:
                    # We do.
                    try:
                        output = self._handlers[lang].call(self, obj, user, args)
                    except python.PythonObjectError as e:
                        self._warn(str(e))
                        if not ignore_object_errors:
                            raise ObjectError(str(e))
                        output = RS_ERR_OBJECT
                else:
                    if not ignore_object_errors:
                        raise ObjectError(RS_ERR_OBJECT_HANDLER)
                    output = RS_ERR_OBJECT_HANDLER
            else:
                if not ignore_object_errors:
                    raise ObjectError(RS_ERR_OBJECT_MISSING)
                output = RS_ERR_OBJECT_MISSING

            reply = reply.replace('<call>{match}</call>'.format(match=match), output)

        return reply

    def _string_format(self, msg, method):
        """Format a string (upper, lower, formal, sentence).

        :param str msg: The user's message.
        :param str method: One of ``uppercase``, ``lowercase``,
            ``sentence`` or ``formal``.

        :return str: The reformatted string.
        """
        if method == "uppercase":
            return msg.upper()
        elif method == "lowercase":
            return msg.lower()
        elif method == "sentence":
            return msg.capitalize()
        elif method == "formal":
            return string.capwords(msg)

    ############################################################################
    # Topic inheritance Utility Methods                                        #
    ############################################################################

    def _topic_triggers(self, topic, triglvl, depth=0, inheritance=0, inherited=False):
        """Recursively scan a topic and return a list of all triggers.

        :param str topic: The original topic name.
        :param dict triglvl: A reference to where the triggers are located,
            e.g. normal triggers vs. ones with ``%Previous``.
        :param int depth: The recursion depth counter.
        :param int inheritance: The inheritance level counter, for topics that
            inherit other topics.
        :param bool inherited: Whether the current topic is inherited by others.

        :return []str: List of all triggers found.
        """

        # Break if we're in too deep.
        if depth > self._depth:
            self._warn("Deep recursion while scanning topic inheritance")

        # Important info about the depth vs inheritance params to this function:
        # depth increments by 1 each time this function recursively calls itself.
        # inheritance increments by 1 only when this topic inherits another
        # topic.
        #
        # This way, '> topic alpha includes beta inherits gamma' will have this
        # effect:
        #  alpha and beta's triggers are combined together into one matching
        #  pool, and then those triggers have higher matching priority than
        #  gamma's.
        #
        # The inherited option is True if this is a recursive call, from a topic
        # that inherits other topics. This forces the {inherits} tag to be added
        # to the triggers. This only applies when the top topic 'includes'
        # another topic.
        self._say("\tCollecting trigger list for topic " + topic + "(depth="
            + str(depth) + "; inheritance=" + str(inheritance) + "; "
            + "inherited=" + str(inherited) + ")")

        # topic:   the name of the topic
        # triglvl: reference to self._topics or self._thats
        # depth:   starts at 0 and ++'s with each recursion

        # Collect an array of triggers to return.
        triggers = []

        # Get those that exist in this topic directly.
        inThisTopic = []
        if topic in triglvl:
            for trigger in triglvl[topic]:
                inThisTopic.append(trigger)

        # Does this topic include others?
        if topic in self._includes:
            # Check every included topic.
            for includes in self._includes[topic]:
                self._say("\t\tTopic " + topic + " includes " + includes)
                triggers.extend(self._topic_triggers(includes, triglvl, (depth + 1), inheritance, True))

        # Does this topic inherit others?
        if topic in self._lineage:
            # Check every inherited topic.
            for inherits in self._lineage[topic]:
                self._say("\t\tTopic " + topic + " inherits " + inherits)
                triggers.extend(self._topic_triggers(inherits, triglvl, (depth + 1), (inheritance + 1), False))

        # Collect the triggers for *this* topic. If this topic inherits any
        # other topics, it means that this topic's triggers have higher
        # priority than those in any inherited topics. Enforce this with an
        # {inherits} tag.
        if topic in self._lineage or inherited:
            for trigger in inThisTopic:
                self._say("\t\tPrefixing trigger with {inherits=" + str(inheritance) + "}" + trigger)
                triggers.append("{inherits=" + str(inheritance) + "}" + trigger)
        else:
            triggers.extend(inThisTopic)

        return triggers

    def _find_trigger_by_inheritance(self, topic, trig, depth=0):
        """Locate the replies for a trigger in an inherited/included topic.

        :param str topic: The topic to search in.
        :param str trig: The trigger we're looking for.
        :param int depth: The recursion depth counter.

        :return dict: The trigger's details.
        """

        # This sub was called because the user matched a trigger from the sorted
        # array, but the trigger doesn't belong to their topic, and is instead
        # in an inherited or included topic. This is to search for it.

        # Prevent recursion.
        if depth > self._depth:
            self._warn("Deep recursion detected while following an inheritance trail!")
            return None

        # inheritance is more important than inclusion: triggers in one topic can
        # override those in an inherited topic.
        if topic in self._lineage:
            for inherits in sorted(self._lineage[topic]):
                # See if this inherited topic has our trigger.
                if trig in self._topics[inherits]:
                    # Great!
                    return self._topics[inherits][trig]
                else:
                    # Check what THAT topic inherits from.
                    match = self._find_trigger_by_inheritance(
                        inherits, trig, (depth + 1)
                    )
                    if match:
                        # Found it!
                        return match

        # See if this topic has an "includes"
        if topic in self._includes:
            for includes in sorted(self._includes[topic]):
                # See if this included topic has our trigger.
                if trig in self._topics[includes]:
                    # Great!
                    return self._topics[includes][trig]
                else:
                    # Check what THAT topic inherits from.
                    match = self._find_trigger_by_inheritance(
                        includes, trig, (depth + 1)
                    )
                    if match:
                        # Found it!
                        return match

        # Don't know what else to do!
        return None

    def _get_topic_tree(self, topic, depth=0):
        """Given one topic, get the list of all included/inherited topics.

        :param str topic: The topic to start the search at.
        :param int depth: The recursion depth counter.

        :return []str: Array of topics.
        """

        # Break if we're in too deep.
        if depth > self._depth:
            self._warn("Deep recursion while scanning topic trees!")
            return []

        # Collect an array of all topics.
        topics = [topic]

        # Does this topic include others?
        if topic in self._includes:
            # Try each of these.
            for includes in sorted(self._includes[topic]):
                topics.extend(self._get_topic_tree(includes, depth + 1))

        # Does this topic inherit others?
        if topic in self._lineage:
            # Try each of these.
            for inherits in sorted(self._lineage[topic]):
                topics.extend(self._get_topic_tree(inherits, depth + 1))

        return topics

    ############################################################################
    # Miscellaneous Private Methods                                            #
    ############################################################################

    def _quotemeta(self, s):
        """Escape a string to make it safe for a regular expression.

        This is used instead of ``self._quotemeta()`` because Python 3.6 obsoleted
        the ``\d`` escape sequence for some reason for that function.

        :param str s: The string to make regexp-safe.
        :return str: The string with all regexp metacharacters escaped.
        """
        unsafe = list(r'\.+?[^]$(){}=!<>|:')
        for char in unsafe:
            s = s.replace(char, "\\{}".format(char))
        return s

    def _is_atomic(self, trigger):
        """Determine if a trigger is atomic or not.

        In this context we're deciding whether or not the trigger needs to use
        the regular expression engine for testing. So any trigger that contains
        nothing but plain words is considered atomic, whereas a trigger with any
        "regexp-like" parts (even alternations) is not.

        :param trigger: The trigger to test.

        :return bool: Whether it's atomic or not.
        """

        # Atomic triggers don't contain any wildcards or parenthesis or anything
        # of the sort. We don't need to test the full character set, just left
        # brackets will do.
        special = ['*', '#', '_', '(', '[', '<', '@']
        for char in special:
            if char in trigger:
                return False

        return True

    def _word_count(self, trigger, all=False):
        """Count the words that aren't wildcards in a trigger.

        :param str trigger: The trigger to count words for.
        :param bool all: Count purely based on whitespace separators, or
            consider wildcards not to be their own words.

        :return int: The word count."""
        words = []
        if all:
            words = re.split(RE.ws, trigger)
        else:
            words = re.split(RE.wilds, trigger)

        wc = 0  # Word count
        for word in words:
            if len(word) > 0:
                wc += 1

        return wc

    def _strip_nasties(self, s):
        """Formats a string for ASCII regex matching."""
        s = re.sub(RE.nasties, '', s)
        return s

    def _dump(self):
        """For debugging, dump the entire data structure."""
        pp = pprint.PrettyPrinter(indent=4)

        print("=== Variables ===")
        print("-- Globals --")
        pp.pprint(self._gvars)
        print("-- Bot vars --")
        pp.pprint(self._bvars)
        print("-- Substitutions --")
        pp.pprint(self._subs)
        print("-- Person Substitutions --")
        pp.pprint(self._person)
        print("-- Arrays --")
        pp.pprint(self._arrays)

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
