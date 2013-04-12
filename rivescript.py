# pyRiveScript - A RiveScript interpreter written in Python.

VERSION = '1.01'

import os
import glob
import re
import string
import random
import pprint
import copy
import codecs

import sys
import getopt
import json

# Common regular expressions.
re_equals  = re.compile('\s*=\s*')
re_ws      = re.compile('\s+')
re_objend  = re.compile('<\s*object')
re_weight  = re.compile('\{weight=(\d+)\}')
re_inherit = re.compile('\{inherits=(\d+)\}')
re_wilds   = re.compile('[\s\*\#\_]+')
re_rot13   = re.compile('<rot13sub>(.+?)<bus31tor>')
re_nasties = re.compile('[^A-Za-z0-9 ]')

# Version of RiveScript we support.
rs_version = 2.0

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
        except:
            reply = '[ERR: Error when executing Python object]'
        return reply

class RiveScript:
    """A RiveScript interpreter for Python 2."""
    _debug    = False # Debug mode
    _utf8     = False # UTF-8 mode
    _strict   = True  # Strict mode
    _logf     = ''    # Log file for debugging
    _depth    = 50    # Recursion depth limit
    _gvars    = {}    # 'global' variables
    _bvars    = {}    # 'bot' variables
    _subs     = {}    # 'sub' variables
    _person   = {}    # 'person' variables
    _arrays   = {}    # 'array' variables
    _users    = {}    # 'user' variables
    _freeze   = {}    # frozen 'user' variables
    _includes = {}    # included topics
    _lineage  = {}    # inherited topics
    _handlers = {}    # Object handlers
    _objlangs = {}    # Languages of objects used
    _topics   = {}    # Main reply structure
    _thats    = {}    # %Previous reply structure
    _sorted   = {}    # Sorted buffers

    ############################################################################
    # Initialization and Utility Methods                                       #
    ############################################################################

    def __init__(self, debug=False, strict=True, depth=50, log="", utf8=False):
        """Initialize a new RiveScript interpreter.

bool debug:  Specify a debug mode.
bool strict: Strict mode (RS syntax errors are fatal)
str  log:    Specify a log file for debug output to go to (instead of STDOUT).
int  depth:  Specify the recursion depth limit.
bool utf8:   Enable UTF-8 support."""
        self._debug  = debug
        self._strict = strict
        self._depth  = depth
        self._log    = log
        self._utf8   = utf8

        # Define the default Python language handler.
        self._handlers["python"] = PyRiveObjects()

        self._say("Interpreter initialized.")

    def _say(self, message):
        if self._debug:
            print "[RS]", message
        if self._log:
            # Log it to the file.
            fh = open(self._log, 'a')
            fh.write("[RS] " + message + "\n")
            fh.close()

    def _warn(self, message, fname='', lineno=0):
        if self._debug:
            print "[RS::Warning]",
        else:
            print "[RS]",
        if len(fname) and lineno > 0:
            print message, "at", fname, "line", lineno
        else:
            print message

    ############################################################################
    # Loading and Parsing Methods                                              #
    ############################################################################

    def load_directory(self, directory, ext='.rs'):
        """Load RiveScript documents from a directory."""
        self._say("Loading from directory: " + directory + "/*" + ext)

        if not os.path.isdir(directory):
            self._warn("Error: " + directory + " is not a directory.")
            return

        for item in glob.glob( os.path.join(directory, '*'+ext) ):
            self.load_file( item )

    def load_file(self, filename):
        """Load and parse a RiveScript document."""
        self._say("Loading file: " + filename)

        fh    = codecs.open(filename, 'r', 'utf-8')
        lines = fh.readlines()
        fh.close()

        self._say("Parsing " + str(len(lines)) + " lines of code from " + filename)
        self._parse(filename, lines)

    def stream(self, code):
        """Stream in RiveScript source code dynamically.

`code` should be an array of lines of RiveScript code."""
        self._say("Streaming code.")
        self._parse("stream()", code)

    def _parse(self, fname, code):
        """Parse RiveScript code into memory."""
        self._say("Parsing code")

        # Track temporary variables.
        topic   = 'random' # Default topic=random
        lineno  = 0        # Line numbers for syntax tracking
        comment = False    # In a multi-line comment
        inobj   = False    # In an object
        objname = ''       # The name of the object we're in
        objlang = ''       # The programming language of the object
        objbuf  = []       # Object contents buffer
        ontrig  = ''       # The current trigger
        repcnt  = 0        # Reply counter
        concnt  = 0        # Condition counter
        lastcmd = ''       # Last command code
        isThat  = ''       # Is a %Previous trigger

        # Read each line.
        for lp, line in enumerate(code):
            lineno = lineno + 1

            self._say("Line: " + line + " (topic: " + topic + ") incomment: " + str(inobj))
            if len(line.strip()) == 0: # Skip blank lines
                continue

            # In an object?
            if inobj:
                if re.match(re_objend, line):
                    # End the object.
                    if len(objname):
                        # Call the object's handler.
                        if objlang in self._handlers:
                            self._objlangs[objname] = objlang;
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

            line   = line.strip() # Trim excess space. We do it down here so we
                                  # don't mess up python objects!

            # Look for comments.
            if line[:2] == '//': # A single-line comment.
                continue
            elif line[0] == '#':
                self._warn("Using the # symbol for comments is deprecated", fname, lineno)
            elif line[:2] == '/*':   # Start of a multi-line comment.
                if not '*/' in line: # Cancel if the end is here too.
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
            cmd  = line[0]
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
                    return # Don't try to continue

            # Reset the %Previous state if this is a new +Trigger.
            if cmd == '+':
                isThat = ''

            # Do a lookahead for ^Continue and %Previous commands.
            for i in range(lp + 1, len(code)):
                lookahead = code[i].strip()
                if len(lookahead) < 2:
                    continue
                lookCmd   = lookahead[0]
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
                            line += lookahead
                        else:
                            break

            self._say("Command: " + cmd + "; line: " + line)

            # Handle the types of RiveScript commands.
            if cmd == '!':
                # ! DEFINE
                halves = re.split(re_equals, line, 2)
                left = re.split(re_ws, halves[0].strip(), 2)
                value, type, var = '', '', ''
                if len(halves) == 2:
                    value = halves[1].strip()
                if len(left) >= 1:
                    type = left[0].strip()
                    if len(left) >= 2:
                        var = ' '.join(left[1:]).strip()

                # Remove 'fake' line breaks unless this is an array.
                if type != 'array':
                    value = re.sub(r'<crlf>', '', value)

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
                if type == 'global':
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
                            fields.extend( val.split('|') )
                        else:
                            fields.extend( re.split(re_ws, val) )

                    # Convert any remaining '\s' escape codes into spaces.
                    for f in fields:
                        f = f.replace(r'\s', ' ')

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
                else:
                    self._warn("Unknown definition type '" + type + "'", fname, lineno)
            elif cmd == '>':
                # > LABEL
                temp = re.split(re_ws, line)
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
                    mode = '' # or 'inherits' or 'includes'
                    if len(fields) >= 2:
                        for field in fields:
                            if field == 'includes':
                                mode = 'includes'
                            elif field == 'inherits':
                                mode = 'inherits'
                            elif mode != '':
                                # This topic is either inherited or included.
                                if mode == 'includes':
                                    if not name in self._includes:
                                        self._includes[name] = {}
                                    self._includes[name][field] = 1
                                else:
                                    if not name in self._lineage:
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
                    if lang == None:
                        self._warn("Trying to parse unknown programming language", fname, fileno)
                        lang = 'python' # Assume it's Python.

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
                else:
                    self._initTT('topics', topic, line)
                ontrig = line
                repcnt = 0
                concnt = 0
            elif cmd == '-':
                # - REPLY
                if ontrig == '':
                    self._warn("Response found before trigger", fname, lineno)
                    continue
                self._say("\tResponse: " + line)
                if len(isThat):
                    self._thats[topic][isThat][ontrig]['reply'][repcnt] = line
                else:
                    self._topics[topic][ontrig]['reply'][repcnt] = line
                repcnt = repcnt + 1
            elif cmd == '%':
                # % PREVIOUS
                pass # This was handled above.
            elif cmd == '^':
                # ^ CONTINUE
                pass # This was handled above.
            elif cmd == '@':
                # @ REDIRECT
                self._say("\tRedirect response to " + line)
                if len(isThat):
                    self._thats[topic][isThat][ontrig]['redirect'] = line
                else:
                    self._topics[topic][ontrig]['redirect'] = line
            elif cmd == '*':
                # * CONDITION
                self._say("\tAdding condition: " + line)
                if len(isThat):
                    self._thats[topic][isThat][ontrig]['condition'][concnt] = line
                else:
                    self._topics[topic][ontrig]['condition'][concnt] = line
                concnt = concnt + 1
            else:
                self._warn("Unrecognized command \"" + cmd + "\"", fname, lineno)
                continue

    def check_syntax(self, cmd, line):
        """Syntax check a RiveScript command and line.

Returns a syntax error string on error; None otherwise."""

        # Run syntax checks based on the type of command.
        if cmd == '!':
            # ! Definition
            #   - Must be formatted like this:
            #     ! type name = value
            #     OR
            #     ! type = value
            match = re.match(r'^.+(?:\s+.+|)\s*=\s*.+?$', line)
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
                rest = ' '.join(parts)
                match = re.match(r'[^a-z0-9_\-\s]', line)
                if match:
                    return "Topics should be lowercased and contain only numbers and letters"
            elif parts[0] == "object":
                rest = ' '.join(parts)
                match = re.match(r'[^A-Za-z0-9_\-\s]', line)
                if match:
                    return "Objects can only contain numbers and letters"
        elif cmd == '+' or cmd == '%' or cmd == '@':
            # + Trigger, % Previous, @ Redirect
            #   This one is strict. The triggers are to be run through the regexp engine,
            #   therefore it should be acceptable for the regexp engine.
            #   - Entirely lowercase
            #   - No symbols except: ( | ) [ ] * _ # @ { } < > =
            #   - All brackets should be matched
            parens = 0 # Open parenthesis
            square = 0 # Open square brackets
            curly  = 0 # Open curly brackets
            angle  = 0 # Open angled brackets

            # Look for obvious errors.
            match = re.match(r'[^a-z0-9(|)\[\]*_#@{}<>=\s]', line)
            if match:
                return "Triggers may only contain lowercase letters, numbers, and these symbols: ( | ) [ ] * _ # @ { } < > ="

            # Count brackets.
            for char in line:
                if char == '(':
                    parens = parens + 1
                elif char == ')':
                    parens = parens - 1
                elif char == '[':
                    square = square + 1
                elif char == ']':
                    square = square - 1
                elif char == '{':
                    curly = curly + 1
                elif char == '}':
                    curly = curly - 1
                elif char == '<':
                    angle = angle + 1
                elif char == '>':
                    angle = angle - 1

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
                match = re.match(r'[A-Z\\.]', line)
                if match:
                    return "Triggers can't contain uppercase letters, backslashes or dots in UTF-8 mode."
            else:
                match = re.match(r'[^a-z0-9(\|)\[\]*_#@{}<>=\s]', line)
                if match:
                    return "Triggers may only contain lowercase letters, numbers, and these symbols: ( | ) [ ] * _ # @ { } < > =";
        elif cmd == '-' or cmd == '^' or cmd == '/':
            # - Trigger, ^ Continue, / Comment
            # These commands take verbatim arguments, so their syntax is loose.
            pass
        elif cmd == '*':
            # * Condition
            #   Syntax for a conditional is as follows:
            #   * value symbol value => response
            match = re.match(r'^.+?\s*(?:==|eq|!=|ne|<>|<|<=|>|>=)\s*.+?=>.+?$', line)
            if not match:
                return "Invalid format for !Condition: should be like '* value symbol value => response'"

        return None

    def _initTT(self, toplevel, topic, trigger, what=''):
        """Initialize a Topic Tree data structure."""
        if toplevel == 'topics':
            if not topic in self._topics:
                self._topics[topic] = {}
            if not trigger in self._topics[topic]:
                self._topics[topic][trigger]              = {}
                self._topics[topic][trigger]['reply']     = {}
                self._topics[topic][trigger]['condition'] = {}
                self._topics[topic][trigger]['redirect']  = None
        elif toplevel == 'thats':
            if not topic in self._thats:
                self._thats[topic] = {}
            if not trigger in self._thats[topic]:
                self._thats[topic][trigger] = {}
            if not what in self._thats[topic][trigger]:
                self._thats[topic][trigger][what] = {}
                self._thats[topic][trigger][what]['reply']     = {}
                self._thats[topic][trigger][what]['condition'] = {}
                self._thats[topic][trigger][what]['redirect']  = {}

    ############################################################################
    # Sorting Methods                                                          #
    ############################################################################

    def sort_replies(self, thats=False):
        """Sort the loaded triggers."""
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
            if not sortlvl in self._sorted:
                self._sorted[sortlvl] = {}
            self._sorted[sortlvl][topic] = running

        # And do it all again for %Previous!
        if thats != True:
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

        if not "that_trig" in self._sorted:
            self._sorted["that_trig"] = {}

        for topic in self._thats:
            if not topic in self._sorted["that_trig"]:
                self._sorted["that_trig"][topic] = {}

            for bottrig in self._thats[topic]:
                if not bottrig in self._sorted["that_trig"][topic]:
                    self._sorted["that_trig"][topic][bottrig] = []
                triggers = self._sort_trigger_set(self._thats[topic][bottrig].keys())
                self._sorted["that_trig"][topic][bottrig] = triggers

    def _sort_trigger_set(self, triggers):
        """Sort a group of triggers in optimal sorting order."""

        # Create a priority map.
        prior = {
            0: [] # Default priority=0
        }

        for trig in triggers:
            match, weight = re.search(re_weight, trig), 0
            if match:
                weight = int(match.group(1))
            if not weight in prior:
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
            inherits = -1         # -1 means no {inherits} tag
            highest_inherits = -1 # highest inheritence number seen

            # Loop through and categorize these triggers.
            track = {
                inherits: self._init_sort_track()
            }

            for trig in prior[p]:
                self._say("\t\tLooking at trigger: " + trig)

                # See if it has an inherits tag.
                match = re.search(re_inherit, trig)
                if match:
                    inherits = int(match.group(1))
                    if inherits > highest_inherits:
                        highest_inherits = inherits
                    self._say("\t\t\tTrigger belongs to a topic which inherits other topics: level=" + str(inherits))
                    trig = re.sub(re_inherit, "", trig)
                else:
                    inherits = -1

                # If this is the first time we've seen this inheritence level,
                # initialize its track structure.
                if not inherits in track:
                    track[inherits] = self._init_sort_track()

                # Start inspecting the trigger's contents.
                if '_' in trig:
                    # Alphabetic wildcard included.
                    cnt = self._word_count(trig)
                    self._say("\t\t\tHas a _ wildcard with " + str(cnt) + " words.")
                    if cnt > 1:
                        if not cnt in track[inherits]['alpha']:
                            track[inherits]['alpha'][cnt] = []
                        track[inherits]['alpha'][cnt].append(trig)
                    else:
                        track[inherits]['under'].append(trig)
                elif '#' in trig:
                    # Numeric wildcard included.
                    cnt = self._word_count(trig)
                    self._say("\t\t\tHas a # wildcard with " + str(cnt) + " words.")
                    if cnt > 1:
                        if not cnt in track[inherits]['number']:
                            track[inherits]['number'][cnt] = []
                        track[inherits]['number'][cnt].append(trig)
                    else:
                        track[inherits]['pound'].append(trig)
                elif '*' in trig:
                    # Wildcard included.
                    cnt = self._word_count(trig)
                    self._say("\t\t\tHas a * wildcard with " + str(cnt) + " words.")
                    if cnt > 1:
                        if not cnt in track[inherits]['wild']:
                            track[inherits]['wild'][cnt] = []
                        track[inherits]['wild'][cnt].append(trig)
                    else:
                        track[inherits]['star'].append(trig)
                elif '[' in trig:
                    # Optionals included.
                    cnt = self._word_count(trig)
                    self._say("\t\t\tHas optionals and " + str(cnt) + " words.")
                    if not cnt in track[inherits]['option']:
                        track[inherits]['option'][cnt] = []
                    track[inherits]['option'][cnt].append(trig)
                else:
                    # Totally atomic.
                    cnt = self._word_count(trig)
                    self._say("\t\t\tTotally atomic and " + str(cnt) + " words.")
                    if not cnt in track[inherits]['atomic']:
                        track[inherits]['atomic'][cnt] = []
                    track[inherits]['atomic'][cnt].append(trig)

            # Move the no-{inherits} triggers to the bottom of the stack.
            track[ (highest_inherits + 1) ] = track[-1]
            del(track[-1])

            # Add this group to the sort list.
            for ip in sorted(track.keys()):
                self._say("ip=" + str(ip))
                for kind in [ 'atomic', 'option', 'alpha', 'number', 'wild' ]:
                    for i in sorted(track[ip][kind], reverse=True):
                        running.extend( track[ip][kind][i] )
                running.extend( sorted(track[ip]['under'], key=len, reverse=True) )
                running.extend( sorted(track[ip]['pound'], key=len, reverse=True) )
                running.extend( sorted(track[ip]['star'], key=len, reverse=True) )
        return running

    def _sort_list(self, name, items):
        """Sort a simple list by number of words and length."""

        def by_length(word1, word2):
            return len(word2)-len(word1)

        # Initialize the list sort buffer.
        if not "lists" in self._sorted:
            self._sorted["lists"] = {}
        self._sorted["lists"][name] = []

        # Track by number of words.
        track = {}

        # Loop through each item.
        for item in items:
            # Count the words.
            cword = self._word_count(item, all=True)
            if not cword in track:
                track[cword] = []
            track[cword].append(item)

        # Sort them.
        output = []
        for count in sorted(track.keys(), reverse=True):
            sort = sorted(track[count], cmp=by_length)
            output.extend(sort)

        self._sorted["lists"][name] = output

    def _init_sort_track(self):
        """Returns a new dict for keeping track of triggers for sorting."""
        return {
            'atomic': {}, # Sort by number of whole words
            'option': {}, # Sort optionals by number of words
            'alpha':  {}, # Sort alpha wildcards by no. of words
            'number': {}, # Sort number wildcards by no. of words
            'wild':   {}, # Sort wildcards by no. of words
            'pound':  [], # Triggers of just #
            'under':  [], # Triggers of just _
            'star':   []  # Triggers of just *
        }


    ############################################################################
    # Public Configuration Methods                                             #
    ############################################################################

    def set_handler(self, language, obj):
        """Define a custom language handler for RiveScript objects.

language: The lowercased name of the programming language,
          e.g. python, javascript, perl
obj:      An instance of a class object that provides the following interface:

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

Pass in a None value for the object to delete an existing handler (for example,
to prevent Python code from being able to be run by default).

Look in the `eg` folder of the rivescript-python distribution for an example
script that sets up a JavaScript language handler."""

        # Allow them to delete a handler too.
        if obj == None:
            if language in self._handlers:
                del self._handlers[language]
        else:
            self._handlers[language] = obj

    def set_subroutine(self, name, code):
        """Define a Python object from your program.

This is equivalent to having an object defined in the RiveScript code, except
your Python code is defining it instead. `name` is the name of the object, and
`code` is a Python function (a `def`) that accepts rs,args as its parameters.

This method is only available if there is a Python handler set up (which there
is by default, unless you've called set_handler("python", None))."""

        # Do we have a Python handler?
        if 'python' in self._handlers:
            self._handlers['python']._objects[name] = code
        else:
            self._warn("Can't set_subroutine: no Python object handler!")

    def set_global(self, name, value):
        """Set a global variable.

Equivalent to `! global` in RiveScript code. Set to None to delete."""
        if value == None:
            # Unset the variable.
            if name in self._gvars:
                del self._gvars[name]
        self._gvars[name] = value

    def set_variable(self, name, value):
        """Set a bot variable.

Equivalent to `! var` in RiveScript code. Set to None to delete."""
        if value == None:
            # Unset the variable.
            if name in self._bvars:
                del self._bvars[name]
        self._bvars[name] = value

    def set_substitution(self, what, rep):
        """Set a substitution.

Equivalent to `! sub` in RiveScript code. Set to None to delete."""
        if rep == None:
            # Unset the variable.
            if what in self._subs:
                del self._subs[what]
        self._subs[what] = rep

    def set_person(self, what, rep):
        """Set a person substitution.

Equivalent to `! person` in RiveScript code. Set to None to delete."""
        if rep == None:
            # Unset the variable.
            if what in self._person:
                del self._person[what]
        self._person[what] = rep

    def set_uservar(self, user, name, value):
        """Set a variable for a user."""

        if not user in self._users:
            self._users[user] = {"topic": "random"}

        self._users[user][name] = value

    def get_uservar(self, user, name):
        """Get a variable about a user.

If the user has no data at all, returns None. If the user doesn't have a value
set for the variable you want, returns the string 'undefined'."""

        if user in self._users:
            if name in self._users[user]:
                return self._users[user][name]
            else:
                return "undefined"
        else:
            return None

    def get_uservars(self, user=None):
        """Get all variables about a user (or all users).

If no username is passed, returns the entire user database structure. Otherwise,
only returns the variables for the given user, or None if none exist."""

        if user == None:
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

If no username is passed, deletes all variables about all users. Otherwise, only
deletes all variables for the given user."""

        if user == None:
            # All the users!
            self._users = {}
        elif user in self._users:
            # Just this one.
            self._users[user] = {}

    def freeze_uservars(self, user):
        """Freeze the variable state for a user.

This will clone and preserve a user's entire variable state, so that it can be
restored later with `thaw_uservars`."""

        if user in self._users:
            # Clone the user's data.
            self._freeze[user] = copy.deepcopy(self._users[user])
        else:
            self._warn("Can't freeze vars for user " + user + ": not found!")

    def thaw_uservars(self, user, action="thaw"):
        """Thaw a user's frozen variables.

The `action` can be one of the following options:

    discard: Don't restore the user's variables, just delete the frozen copy.
    keep:    Keep the frozen copy after restoring the variables.
    thaw:    Restore the variables, then delete the frozen copy (default)."""

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

This will return the raw trigger text that the user's last message matched. If
there was no match, this will return None."""
        return self.get_uservar(user, "__lastmatch__")

    ############################################################################
    # Reply Fetching Methods                                                   #
    ############################################################################

    def reply(self, user, msg):
        """Fetch a reply from the RiveScript brain."""
        self._say("Get reply to [" + user + "] " + msg)

        # Format their message.
        msg = self._format_message(msg)

        reply = ''

        # If the BEGIN block exists, consult it first.
        if "__begin__" in self._topics:
            begin = self._getreply(user, 'request', context='begin')

            # Okay to continue?
            if '{ok}' in begin:
                reply = self._getreply(user, msg)
                begin = re.sub('{ok}', reply, begin)

            reply = begin

            # Run more tag substitutions.
            reply = self._process_tags(user, msg, reply)
        else:
            # Just continue then.
            reply = self._getreply(user, msg)

        # Save their reply history.
        oldInput = self._users[user]['__history__']['input'][:8]
        self._users[user]['__history__']['input'] = [ msg ]
        self._users[user]['__history__']['input'].extend(oldInput)
        oldReply = self._users[user]['__history__']['reply'][:8]
        self._users[user]['__history__']['reply'] = [ reply ]
        self._users[user]['__history__']['reply'].extend(oldReply)

        return reply

    def _format_message(self, msg):
        """Format a user's message for safe processing."""

        # Lowercase it.
        msg = msg.lower()

        # Run substitutions on it.
        msg = self._substitute(msg, "subs")

        # In UTF-8 mode, only strip metacharacters and HTML brackets
        # (to protect from obvious XSS attacks).
        if self._utf8:
            msg = re.sub(r'[\\<>]', '', msg)
        else:
            # For everything else, strip all non-alphanumerics.
            msg = self._strip_nasties(msg)

        return msg

    def _getreply(self, user, msg, context='normal', step=0):
        # Needed to sort replies?
        if not 'topics' in self._sorted:
            raise Exception("You forgot to call sort_replies()!")

        # Initialize the user's profile?
        if not user in self._users:
            self._users[user] = {'topic': 'random'}

        # Collect data on the user.
        topic     = self._users[user]['topic']
        stars     = []
        thatstars = [] # For %Previous's.
        reply     = ''

        # Avoid letting them fall into a missing topic.
        if not topic in self._topics:
            self._warn("User " + user + " was in an empty topic named '" + topic + "'")
            topic = self._users[user]['topic'] = 'random'

        # Avoid deep recursion.
        if step > self._depth:
            return "ERR: Deep Recursion Detected"

        # Are we in the BEGIN statement?
        if context == 'begin':
            topic = '__begin__'

        # Initialize this user's history.
        if not '__history__' in self._users[user]:
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
        if not topic in self._topics:
            # This was handled before, which would mean topic=random and
            # it doesn't exist. Serious issue!
            return "[ERR: No default topic 'random' was found!]"

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
            allTopics = [ topic ]
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
                    lastReply = self._format_message(lastReply)

                    self._say("lastReply: " + lastReply)

                    # See if it's a match.
                    for trig in self._sorted["thats"][top]:
                        botside = self._reply_regexp(user, trig)
                        self._say("Try to match lastReply (" + lastReply + ") to " + botside)

                        # Match??
                        match = re.match(r'^' + botside + r'$', lastReply)
                        if match:
                            # Huzzah! See if OUR message is right too.
                            self._say("Bot side matched!")
                            thatstars = match.groups()
                            for subtrig in self._sorted["that_trig"][top][trig]:
                                humanside = self._reply_regexp(user, subtrig)
                                self._say("Now try to match " + msg + " to " + humanside)

                                match = re.match(r'^' + humanside + '$', msg)
                                if match:
                                    self._say("Found a match!")
                                    matched = self._thats[top][trig][subtrig]
                                    matchedTrigger = top
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
                if not self._utf8:
                    # This line currently breaks with Unicode strings (bug/TODO), so don't print it
                    self._say("Try to match \"" + msg + "\" against " + trig + " (" + regexp + ")")

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
                    match = re.match(r'^' + regexp + r'$', msg)
                    if match:
                        # The regexp matched!
                        isMatch = True

                        # Collect the stars.
                        stars = match.groups()

                if isMatch:
                    self._say("Found a match!")

                    # We found a match, but what if the trigger we've matched
                    # doesn't belong to our topic? Find it!
                    if not trig in self._topics[topic]:
                        # We have to find it.
                        matched = self._find_trigger_by_inheritence(topic, trig)
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
                    redirect = self._process_tags(user, msg, matched["redirect"], stars, thatstars, step)
                    self._say("Pretend user said: " + redirect)
                    reply = self._getreply(user, redirect, step=(step+1))
                    break

                # Check the conditionals.
                for con in sorted(matched["condition"]):
                    halves = re.split(r'\s*=>\s*', matched["condition"][con])
                    if halves and len(halves) == 2:
                        condition = re.match(r'^(.+?)\s+(==|eq|!=|ne|<>|<|<=|>|>=)\s+(.+?)$', halves[0])
                        if condition:
                            left     = condition.group(1)
                            eq       = condition.group(2)
                            right    = condition.group(3)
                            potreply = halves[1]
                            self._say("Left: " + left + "; eq: " + eq + "; right: " + right + " => " + potreply)

                            # Process tags all around.
                            left  = self._process_tags(user, msg, left, stars, thatstars, step)
                            right = self._process_tags(user, msg, right, stars, thatstars, step)

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
                    match  = re.match(re_weight, text)
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
            reply = "ERR: No Reply Matched"
        elif len(reply) == 0:
            reply = "ERR: No Reply Found"

        self._say("Reply: " + reply)

        # Process tags for the BEGIN block.
        if context == "begin":
            # BEGIN blocks can only set topics and uservars. The rest happen
            # later!
            reTopic = re.findall(r'\{topic=(.+?)\}', reply)
            for match in reTopic:
                self._say("Setting user's topic to " + match)
                self._users[user]["topic"] = match
                reply = re.sub(r'\{topic=' + re.escape(match) + r'\}', '', reply)

            reSet = re.findall('<set (.+?)=(.+?)>', reply)
            for match in reSet:
                self._say("Set uservar " + str(match[0]) + "=" + str(match[1]))
                self._users[user][ match[0] ] = match[1]
                reply = re.sub('<set ' + re.escape(match[0]) + '=' + re.escape(match[1]) + '>', '', reply)
        else:
            # Process more tags if not in BEGIN.
            reply = self._process_tags(user, msg, reply, stars, thatstars, step)

        return reply

    def _substitute(self, msg, list):
        """Run a kind of substitution on a message."""

        # Safety checking.
        if not 'lists' in self._sorted:
            raise Exception("You forgot to call sort_replies()!")
        if not list in self._sorted["lists"]:
            raise Exception("You forgot to call sort_replies()!")

        # Get the substitution map.
        subs = None
        if list == 'subs':
            subs = self._subs
        else:
            subs = self._person

        for pattern in self._sorted["lists"][list]:
            result = "<rot13sub>" + self._rot13(subs[pattern]) + "<bus31tor>"
            qm     = re.escape(pattern)
            msg    = re.sub(r'^' + qm + "$", result, msg)
            msg    = re.sub(r'^' + qm + r'(\W+)', result+r'\1', msg)
            msg    = re.sub(r'(\W+)' + qm + r'(\W+)', r'\1'+result+r'\2', msg)
            msg    = re.sub(r'(\W+)' + qm + r'$', r'\1'+result, msg)

        placeholders = re.findall(re_rot13, msg)
        for match in placeholders:
            rot13   = match
            decoded = self._rot13(match)
            msg     = re.sub('<rot13sub>' + re.escape(rot13) + '<bus31tor>', decoded, msg)

        # Strip & return.
        return msg.strip()

    def _reply_regexp(self, user, regexp):
        """Prepares a trigger for the regular expression engine."""

        # If the trigger is simply '*' then the * there needs to become (.*?)
        # to match the blank string too.
        regexp = re.sub(r'^\*$', r'<zerowidthstar>', regexp)

        # Simple replacements.
        regexp = re.sub(r'\*', r'(.+?)', regexp) # Convert * into (.+?)
        regexp = re.sub(r'#', r'(\d+?)', regexp) # Convert # into (\d+?)
        regexp = re.sub(r'_', r'([A-Za-z]+?)', regexp) # Convert _ into (\w+?)
        regexp = re.sub(r'\{weight=\d+\}', '', regexp) # Remove {weight} tags
        regexp = re.sub(r'<zerowidthstar>', r'(.*?)', regexp)

        # Optionals.
        optionals = re.findall(r'\[(.+?)\]', regexp)
        for match in optionals:
            parts = match.split("|")
            new   = []
            for p in parts:
                p = r'\s*' + p + r'\s*'
                new.append(p)
            new.append(r'\s*')

            # If this optional had a star or anything in it, make it
            # non-matching.
            pipes = '|'.join(new)
            pipes = re.sub(re.escape('(.+?)'), '(?:.+?)', pipes)
            pipes = re.sub(re.escape('(\d+?)'), '(?:\d+?)', pipes)
            pipes = re.sub(re.escape('([A-Za-z]+?)'), '(?:[A-Za-z]+?)', pipes)

            regexp = re.sub(r'\s*\[' + re.escape(match) + '\]\s*', '(?:' + pipes + ')', regexp)

        # Filter in arrays.
        arrays = re.findall(r'\@(.+?)\b', regexp)
        for array in arrays:
            rep = ''
            if array in self._arrays:
                rep = r'(?:' + '|'.join(self._arrays[array]) + ')'
            regexp = re.sub(r'\@' + re.escape(array) + r'\b', rep, regexp)

        # Filter in bot variables.
        bvars = re.findall(r'<bot (.+?)>', regexp)
        for var in bvars:
            rep = ''
            if var in self._bvars:
                rep = self._strip_nasties(self._bvars[var])
            regexp = re.sub(r'<bot ' + re.escape(var) + r'>', rep, regexp)

        # Filter in user variables.
        uvars = re.findall(r'<get (.+?)>', regexp)
        for var in uvars:
            rep = ''
            if var in self._users[user]:
                rep = self._strip_nasties(self._users[user][var])
            regexp = re.sub(r'<get ' + re.escape(var) + r'>', rep, regexp)

        # Filter in <input> and <reply> tags. This is a slow process, so only
        # do it if we have to!
        if '<input' in regexp or '<reply' in regexp:
            for type in ['input','reply']:
                tags = re.findall(r'<' + type + r'([0-9])>', regexp)
                for index in tags:
                    index = int(index) - 1
                    rep = self._format_message(self._users[user]['__history__'][type][index])
                    regexp = re.sub(r'<' + type + str(index) + r'>', rep, regexp)
                regexp = re.sub(
                    '<' + type + '>',
                    self._format_message(self._users[user]['__history__'][type][0]),
                    regexp
                )
                # TODO: the Perl version doesn't do just <input>/<reply> in trigs!

        return regexp

    def _process_tags(self, user, msg, reply, st=[], bst=[], depth=0):
        """Post process tags in a message."""
        stars    = ['']
        stars.extend(st)
        botstars = ['']
        botstars.extend(bst)
        if len(stars) == 1:
            stars.append("undefined")
        if len(botstars) == 1:
            botstars.append("undefined")

        # Tag shortcuts.
        reply = re.sub('<person>', '{person}<star>{/person}', reply)
        reply = re.sub('<@>', '{@<star>}', reply)
        reply = re.sub('<formal>', '{formal}<star>{/formal}', reply)
        reply = re.sub('<sentence>', '{sentence}<star>{/sentence}', reply)
        reply = re.sub('<uppercase>', '{uppercase}<star>{/uppercase}', reply)
        reply = re.sub('<lowercase>', '{lowercase}<star>{/lowercase}', reply)

        # Weight and <star> tags.
        reply = re.sub(r'\{weight=\d+\}', '', reply) # Leftover {weight}s
        if len(stars) > 0:
            reply = re.sub('<star>', stars[1], reply)
            reStars = re.findall(r'<star(\d+)>', reply)
            for match in reStars:
                if int(match) < len(stars):
                    reply = re.sub(r'<star' + match + '>', stars[int(match)], reply)
        if len(botstars) > 0:
            reply = re.sub('<botstar>', botstars[1], reply)
            reStars = re.findall(r'<botstar(\d+)>', reply)
            for match in reStars:
                if int(match) < len(botstars):
                    reply = re.sub(r'<botstar' + match + '>', botstars[int(match)], reply)

        # <input> and <reply>
        reply = re.sub('<input>', self._users[user]['__history__']['input'][0], reply)
        reply = re.sub('<reply>', self._users[user]['__history__']['reply'][0], reply)
        reInput = re.findall(r'<input([0-9])>', reply)
        for match in reInput:
            reply = re.sub(r'<input' + match + r'>', self._users[user]['__history__']['input'][int(match)], reply)
        reReply = re.findall(r'<reply([0-9])>', reply)
        for match in reReply:
            reply = re.sub(r'<reply' + match + r'>', self._users[user]['__history__']['reply'][int(match)], reply)

        # <id> and escape codes.
        reply = re.sub(r'<id>', user, reply)
        reply = re.sub(r'\\s', ' ', reply)
        reply = re.sub(r'\\n', "\n", reply)
        reply = re.sub(r'\\#', r'#', reply)

        # Random bits.
        reRandom = re.findall(r'\{random\}(.+?)\{/random\}', reply)
        for match in reRandom:
            output = ''
            if '|' in match:
                output = random.choice(match.split('|'))
            else:
                output = random.choice(match.split(' '))
            reply = re.sub(r'\{random\}' + re.escape(match) + r'\{/random\}', output, reply)

        # Person Substitutions and String Formatting.
        for item in ['person','formal','sentence','uppercase','lowercase']:
            matcher = re.findall(r'\{' + item + r'\}(.+?)\{/' + item + r'\}', reply)
            for match in matcher:
                output = None
                if item == 'person':
                    # Person substitutions.
                    output = self._substitute(match, "person")
                else:
                    output = self._string_format(match, item)
                reply = re.sub(r'\{' + item + r'\}' + re.escape(match) + '\{/' + item + r'\}', output, reply)

        # Bot variables: set (TODO: Perl RS doesn't support this)
        reBotSet = re.findall(r'<bot (.+?)=(.+?)>', reply)
        for match in reBotSet:
            self._say("Set bot variable " + str(match[0]) + "=" + str(match[1]))
            self._bvars[ match[0] ] = match[1]
            reply = re.sub(r'<bot ' + re.escape(match[0]) + '=' + re.escape(match[1]) + '>', '', reply)

        # Bot variables: get
        reBot = re.findall(r'<bot (.+?)>', reply)
        for match in reBot:
            val = 'undefined'
            if match in self._bvars:
                val = self._bvars[match]
            reply = re.sub(r'<bot ' + re.escape(match) + '>', val, reply)

        # Global vars: set (TODO: Perl RS doesn't support this)
        reEnvSet = re.findall(r'<env (.+?)=(.+?)>', reply)
        for match in reEnvSet:
            self._say("Set global variable " + str(match[0]) + "=" + str(match[1]))
            self._gvars[ match[0] ] = match[1]
            reply = re.sub(r'<env ' + re.escape(match[0]) + '=' + re.escape(match[1]) + '>', '', reply)

        # Global vars
        reEnv = re.findall(r'<env (.+?)>', reply)
        for match in reEnv:
            val = 'undefined'
            if match in self._gvars:
                val = self._gvars[match]
            reply = re.sub(r'<env ' + re.escape(match) + '>', val, reply)

        # Streaming code. DEPRECATED!
        if '{!' in reply:
            self._warn("Use of the {!...} tag is deprecated and not supported here.")

        # Set user vars.
        reSet = re.findall('<set (.+?)=(.+?)>', reply)
        for match in reSet:
            self._say("Set uservar " + str(match[0]) + "=" + str(match[1]))
            self._users[user][ match[0] ] = match[1]
            reply = re.sub('<set ' + re.escape(match[0]) + '=' + re.escape(match[1]) + '>', '', reply)

        # Math tags.
        for item in ['add','sub','mult','div']:
            matcher = re.findall('<' + item + r' (.+?)=(.+?)>', reply)
            for match in matcher:
                var    = match[0]
                value  = match[1]
                output = ''

                # Sanity check the value.
                try:
                    value = int(value)

                    # So far so good, initialize this one?
                    if not var in self._users[user]:
                        self._users[user][var] = 0
                except:
                    output = "[ERR: Math can't '" + item + "' non-numeric value '" + value + "']"

                # Attempt the operation.
                try:
                    orig = int(self._users[user][var])
                    new  = 0
                    if item == 'add':
                        new = orig + value
                    elif item == 'sub':
                        new = orig - value
                    elif item == 'mult':
                        new = orig * value
                    elif item == 'div':
                        new = orig / value
                    self._users[user][var] = new
                except:
                    output = "[ERR: Math couldn't '" + item + "' to value '" + self._users[user][var] + "']"

                reply = re.sub('<' + item + ' ' + re.escape(var) + '=' + re.escape(str(value)) + '>', output, reply)

        # Get user vars.
        reGet = re.findall(r'<get (.+?)>', reply)
        for match in reGet:
            output = 'undefined'
            if match in self._users[user]:
                output = self._users[user][match]
            reply = re.sub('<get ' + re.escape(match) + '>', str(output), reply)

        # Topic setter.
        reTopic = re.findall(r'\{topic=(.+?)\}', reply)
        for match in reTopic:
            self._say("Setting user's topic to " + match)
            self._users[user]["topic"] = match
            reply = re.sub(r'\{topic=' + re.escape(match) + r'\}', '', reply)

        # Inline redirecter.
        reRedir = re.findall(r'\{@(.+?)\}', reply)
        for match in reRedir:
            self._say("Redirect to " + match)
            at = match.strip()
            subreply = self._getreply(user, at, step=(depth + 1))
            reply = re.sub(r'\{@' + re.escape(match) + r'\}', subreply, reply)

        # Object caller.
        reCall = re.findall(r'<call>(.+?)</call>', reply)
        for match in reCall:
            parts  = re.split(re_ws, match)
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
                    output = self._handlers[lang].call(self, obj, args)
                else:
                    output = '[ERR: No Object Handler]'
            else:
                output = '[ERR: Object Not Found]'

            reply = re.sub('<call>' + re.escape(match) + r'</call>', output, reply)

        return reply

    def _string_format(self, msg, method):
        """Format a string (upper, lower, formal, sentence)."""
        if method == "uppercase":
            return msg.upper()
        elif method == "lowercase":
            return msg.lower()
        elif method == "sentence":
            return msg.capitalize()
        elif method == "formal":
            return string.capwords(msg)

    ############################################################################
    # Topic Inheritence Utility Methods                                        #
    ############################################################################

    def _topic_triggers(self, topic, triglvl, depth=0, inheritence=0, inherited=False):
        """Recursively scan a topic and return a list of all triggers."""

        # Break if we're in too deep.
        if depth > self._depth:
            self._warn("Deep recursion while scanning topic inheritence")

        # Important info about the depth vs inheritence params to this function:
        # depth increments by 1 each time this function recursively calls itself.
        # inheritence increments by 1 only when this topic inherits another
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
        self._say("\tCollecting trigger list for topic " + topic + "(depth=" \
            + str(depth) + "; inheritence=" + str(inheritence) + "; " \
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
                triggers.extend(self._topic_triggers(includes, triglvl, (depth + 1), inheritence, True))

        # Does this topic inherit others?
        if topic in self._lineage:
            # Check every inherited topic.
            for inherits in self._lineage[topic]:
                self._say("\t\tTopic " + topic + " inherits " + inherits)
                triggers.extend(self._topic_triggers(inherits, triglvl, (depth + 1), (inheritence + 1), False))

        # Collect the triggers for *this* topic. If this topic inherits any
        # other topics, it means that this topic's triggers have higher
        # priority than those in any inherited topics. Enforce this with an
        # {inherits} tag.
        if topic in self._lineage or inherited:
            for trigger in inThisTopic:
                self._say("\t\tPrefixing trigger with {inherits=" + str(inheritence) + "}" + trigger)
                triggers.append("{inherits=" + str(inheritence) + "}" + trigger)
        else:
            triggers.extend(inThisTopic)

        return triggers

    def _find_trigger_by_inheritence(self, topic, trig, depth=0):
        """Locate the replies for a trigger in an inherited/included topic."""

        # This sub was called because the user matched a trigger from the sorted
        # array, but the trigger doesn't belong to their topic, and is instead
        # in an inherited or included topic. This is to search for it.

        # Prevent recursion.
        if depth > self._depth:
            self._warn("Deep recursion detected while following an inheritence trail!")
            return None

        # Inheritence is more important than inclusion: triggers in one topic can
        # override those in an inherited topic.
        if topic in self._lineage:
            for inherits in sorted(self._lineage[topic]):
                # See if this inherited topic has our trigger.
                if trig in self._topics[inherits]:
                    # Great!
                    return self._topics[inherits][trig]
                else:
                    # Check what THAT topic inherits from.
                    match = self._find_trigger_by_inheritence(
                        inherits, trig, (depth+1)
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
                    match = self._find_trigger_by_inheritence(
                        includes, trig, (depth+1)
                    )
                    if match:
                        # Found it!
                        return match

        # Don't know what else to do!
        self._warn("User matched a trigger, " + trig + ", but I can't find out what topic it belongs to!")
        return None

    def _get_topic_tree(self, topic, depth=0):
        """Given one topic, get the list of all included/inherited topics."""

        # Break if we're in too deep.
        if depth > self._depth:
            self._warn("Deep recursion while scanning topic trees!")
            return []

        # Collect an array of all topics.
        topics = [ topic ]

        # Does this topic include others?
        if topic in self._includes:
            # Try each of these.
            for includes in sorted(self._includes[topic]):
                topics.extend( self._get_topic_tree(includes, depth+1) )

        # Does this topic inherit others?
        if topic in self._lineage:
            # Try each of these.
            for inherits in sorted(self._lineage[topic]):
                topics.extend( self._get_topic_tree(inherits, depth+1) )

        return topics

    ############################################################################
    # Miscellaneous Private Methods                                            #
    ############################################################################

    def _is_atomic(self, trigger):
        """Determine if a trigger is atomic or not."""

        # Atomic triggers don't contain any wildcards or parenthesis or anything
        # of the sort. We don't need to test the full character set, just left
        # brackets will do.
        special = [ '*', '#', '_', '(', '[', '<' ]
        for char in special:
            if char in trigger:
                return False

        return True

    def _word_count(self, trigger, all=False):
        """Count the words that aren't wildcards in a trigger."""
        words = []
        if all:
            words = re.split(re_ws, trigger)
        else:
            words = re.split(re_wilds, trigger)

        wc = 0 # Word count
        for word in words:
            if len(word) > 0:
                wc += 1

        return wc

    def _rot13(self, n):
        """Encode and decode a string into ROT13."""
        trans = string.maketrans(
            "ABCDEFGHIJKLMabcdefghijklmNOPQRSTUVWXYZnopqrstuvwxyz",
            "NOPQRSTUVWXYZnopqrstuvwxyzABCDEFGHIJKLMabcdefghijklm")
        return string.translate(str(n), trans)

    def _strip_nasties(self, s):
        """Formats a string for ASCII regex matching."""
        s = re.sub(re_nasties, '', s)
        return s

    def _dump(self):
        """For debugging, dump the entire data structure."""
        pp = pprint.PrettyPrinter(indent=4)

        print "=== Variables ==="
        print "-- Globals --"
        pp.pprint(self._gvars)
        print "-- Bot vars --"
        pp.pprint(self._bvars)
        print "-- Substitutions --"
        pp.pprint(self._subs)
        print "-- Person Substitutions --"
        pp.pprint(self._person)
        print "-- Arrays --"
        pp.pprint(self._arrays)

        print "=== Topic Structure ==="
        pp.pprint(self._topics)
        print "=== %Previous Structure ==="
        pp.pprint(self._thats)

        print "=== Includes ==="
        pp.pprint(self._includes)

        print "=== Inherits ==="
        pp.pprint(self._lineage)

        print "=== Sort Buffer ==="
        pp.pprint(self._sorted)

################################################################################
# Interactive Mode                                                             #
################################################################################

def json_in(bot, buffer, stateful):
    # Prepare the response.
    resp = {
        'status': 'ok',
        'reply': '',
        'vars': {}
    }

    # Decode the incoming JSON.
    try:
        incoming = json.loads(buffer)
    except:
        resp['status'] = 'error'
        resp['reply'] = 'Failed to decode incoming JSON data.'
        print json.dumps(resp)
        if stateful:
            print "__END__"
        return

    # Username?
    username = "json"
    if 'username' in incoming:
        username = incoming["username"]

    # Decode their variables.
    if "vars" in incoming:
        for var in incoming["vars"]:
            bot.set_uservar(username, var, incoming["vars"][var])

    # Get a response.
    if 'message' in incoming:
        resp['reply'] = bot.reply(username, incoming["message"])
    else:
        resp['reply'] = "[ERR: No message provided]"

    # Retrieve vars.
    resp['vars'] = bot.get_uservars(username)

    print json.dumps(resp)
    if stateful:
        print "__END__"

if __name__ == "__main__":
    # Get command line options.
    options, remainder = [], []
    try:
        options, remainder = getopt.getopt(sys.argv[1:], 'dju', ['debug',
                                                                'utf8',
                                                                'json',
                                                                'log=',
                                                                'strict',
                                                                'nostrict',
                                                                'depth=',
                                                                'help'])
    except:
        print "Unrecognized options given, try " + sys.argv[0] + " --help"
        exit()

    # Handle the options.
    debug, depth, strict = False, 50, True
    with_json, help, log = False, False, None
    utf8 = False
    for opt in options:
        if opt[0] == '--debug' or opt[0] == '-d':
            debug = True
        elif opt[0] == '--utf8' or opt[0] == '-u':
            utf8 = True
        elif opt[0] == '--strict':
            strict = True
        elif opt[0] == '--nostrict':
            strict = False
        elif opt[0] == '--json':
            with_json = True
        elif opt[0] == '--help' or opt[0] == '-h':
            help = True
        elif opt[0] == '--depth':
            depth = int(opt[1])
        elif opt[0] == '--log':
            log   = opt[1]

    # Help?
    if help:
        print """Usage: rivescript.py [options] <directory>

Options:

    --debug, -d
        Enable debug mode.

    --log FILE
        Log debug output to a file (instead of the console). Use this instead
        of --debug.

    --json, -j
        Communicate using JSON. Useful for third party programs.

    --strict, --nostrict
        Enable or disable strict mode (enabled by default).

    --depth=50
        Set the recursion depth limit (default is 50).

    --help
        Display this help.

JSON Mode:

    In JSON mode, input and output is done using JSON data structures. The
    format for incoming JSON data is as follows:

    {
        'username': 'localuser',
        'message': 'Hello bot!',
        'vars': {
            'name': 'Aiden'
        }
    }

    The format that would be expected from this script is:

    {
        'status': 'ok',
        'reply': 'Hello, human!',
        'vars': {
            'name': 'Aiden'
        }
    }

    If the calling program sends an EOF signal at the end of their JSON data,
    this script will print its response and exit. To keep a session going,
    send the string '__END__' on a line by itself at the end of your message.
    The script will do the same after its response. The pipe can then be used
    again for further interactions."""
        quit()

    # Given a directory?
    if len(remainder) == 0:
        print "Usage: rivescript.py [options] <directory>"
        print "Try rivescript.py --help"
        quit()
    root = remainder[0]

    # Make the bot.
    bot = RiveScript(
        debug=debug,
        utf8=utf8,
        strict=strict,
        depth=depth,
        log=log
    )
    bot.load_directory(root)
    bot.sort_replies()

    # Interactive mode?
    if with_json:
        # Read from standard input.
        buffer = ""
        stateful = False
        while True:
            line = ""
            try:
                line = raw_input()

                # Support UTF-8 inputs.
                if utf8:
                    line = line.decode('utf-8')
            except EOFError:
                break

            # Look for the __END__ line.
            end = re.match(r'^__END__$', line)
            if end:
                # Process it.
                stateful = True # This is a stateful session
                json_in(bot, buffer, stateful)
                buffer = ""
                continue
            else:
                buffer += line + "\n"

        # We got the EOF. If the session was stateful, just exit,
        # otherwise process what we just read.
        if stateful:
            quit()
        json_in(bot, buffer, stateful)
        quit()

    print "RiveScript Interpreter (Python) -- Interactive Mode"
    print "---------------------------------------------------"
    print "rivescript.py version: " + str(VERSION)
    print "           Reply Root: " + root
    print ""
    print "You are now chatting with the RiveScript bot. Type a message and press Return"
    print "to send it. When finished, type '/quit' to exit the program."
    print "Type '/help' for other options."
    print ""

    while True:
        msg = raw_input("You> ")

        # Support UTF-8 inputs.
        if utf8:
            msg = msg.decode('utf-8')

        # Commands
        if msg == '/help':
            print "> Supported Commands:"
            print "> /help   - Displays this message."
            print "> /quit   - Exit the program."
        elif msg == '/quit':
            exit()
        else:
            reply = bot.reply("localuser", msg)
            print "Bot>", reply

# vim:expandtab
