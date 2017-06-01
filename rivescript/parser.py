# RiveScript-Python
#
# This code is released under the MIT License.
# See the "LICENSE" file for more information.
#
# https://www.rivescript.com/

from __future__ import unicode_literals
from .regexp import RE

import re

# Version of RiveScript we support.
rs_version = 2.0

class Parser(object):
    """The RiveScript language parser.

    This module can be used as a stand-alone parser for third party developers
    to use, if you want to be able to simply parse (and syntax check!)
    RiveScript source code and get an "abstract syntax tree" back from it.

    To that end, this module removed all dependencies on the parent RiveScript
    class. When the RiveScript module uses this module, it passes its own debug
    and warning functions as the ``on_debug`` and ``on_warn`` parameters, but
    these parameters are completely optional.

    Parameters:
        strict (bool): Strict syntax checking (true by default).
        utf8 (bool): Enable UTF-8 mode (false by default).
        on_debug (func): An optional function to send debug messages to. If not
            provided, you won't be able to get debug output from this module.
            The debug function's prototype is: ``def f(message)``
        on_warn (func): An optional function to send warning/error messages to.
            If not provided, you won't be able to get any warnings from
            this module. The warn function's prototype
            is ``def f(message, filename='', lineno='')``
    """

    # Concatenation mode characters.
    concat_modes = dict(
        none="",
        space=" ",
        newline="\n",
    )

    def __init__(self, strict=True, utf8=False, on_debug=None, on_warn=None):
        self.strict   = strict
        self.utf8     = utf8
        self.on_debug = on_debug
        self.on_warn  = on_warn

    # Proxy functions
    def say(self, *args, **kwargs):
        if self.on_debug is not None:
            self.on_debug(*args, **kwargs)

    def warn(self, *args, **kwargs):
        if self.on_warn is not None:
            self.on_warn(*args, **kwargs)

    def parse(self, filename, code):
        """Read and parse a RiveScript document.

        Returns a data structure that represents all of the useful contents of
        the document, in this format::

            {
                "begin": { # "begin" data
                    "global": {}, # map of !global vars
                    "var": {},    # bot !var's
                    "sub": {},    # !sub substitutions
                    "person": {}, # !person substitutions
                    "array": {},  # !array lists
                },
                "topics": { # main reply data
                    "random": { # (topic name)
                        "includes": {}, # map of included topics (values=1)
                        "inherits": {}, # map of inherited topics
                        "triggers": [   # array of triggers
                            {
                                "trigger": "hello bot",
                                "reply": [], # array of replies
                                "condition": [], # array of conditions
                                "redirect": None, # redirect command
                                "previous": None, # 'previous' reply
                            },
                            # ...
                        ]
                    }
                }
                "objects": [ # parsed object macros
                    {
                        "name": "",     # object name
                        "language": "", # programming language
                        "code": [],     # array of lines of code
                    }
                ]
            }

        Args:
            filename (str): The name of the file that the code came from, for
                syntax error reporting purposes.
            code (str[]): The source code to parse.

        Returns:
            dict: The aforementioned data structure.
        """

        # Eventual returned structure ("abstract syntax tree" but not really)
        ast = {
            "begin": {
                "global": {},
                "var": {},
                "sub": {},
                "person": {},
                "array": {},
            },
            "topics": {},
            "objects": [],
        }

        # Track temporary variables.
        topic   = 'random'  # Default topic=random
        lineno  = 0         # Line numbers for syntax tracking
        comment = False     # In a multi-line comment
        inobj   = False     # In an object
        objname = ''        # The name of the object we're in
        objlang = ''        # The programming language of the object
        objbuf  = []        # Object contents buffer
        curtrig = None      # Pointer to the current trigger in ast.topics
        isThat  = None      # Is a %Previous trigger

        # Local (file scoped) parser options.
        local_options = dict(
            concat="none",  # Concat mode for ^Continue command
        )

        # Read each line.
        for lp, line in enumerate(code):
            lineno += 1

            self.say("Line: " + line + " (topic: " + topic + ") incomment: " + str(inobj))
            if len(line.strip()) == 0:  # Skip blank lines
                continue

            # In an object?
            if inobj:
                if re.match(RE.objend, line):
                    # End the object.
                    if len(objname):
                        ast["objects"].append({
                            "name": objname,
                            "language": objlang,
                            "code": objbuf,
                        })
                    objname = ''
                    objlang = ''
                    objbuf  = []
                    inobj   = False
                else:
                    objbuf.append(line)
                continue

            line = line.strip()  # Trim excess space. We do it down here so we
                                 # don't mess up python objects!
            line = RE.ws.sub(" ", line)  # Replace the multiple whitespaces by single whitespace

            # Look for comments.
            if line[:2] == '//':  # A single-line comment.
                continue
            elif line[0] == '#':
                self.warn("Using the # symbol for comments is deprecated", filename, lineno)
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
                self.warn("Weird single-character line '" + line + "' found.", filename, lineno)
                continue
            cmd = line[0]
            line = line[1:].strip()

            # Ignore inline comments if there's a space before the // symbols.
            if " //" in line:
                line = line.split(" //")[0].strip()

            # Run a syntax check on this line.
            syntax_error = self.check_syntax(cmd, line)
            if syntax_error:
                # There was a syntax error! Are we enforcing strict mode?
                syntax_error = "Syntax error in " + filename + " line " + str(lineno) + ": " \
                    + syntax_error + " (near: " + cmd + " " + line + ")"
                if self.strict:
                    raise Exception(syntax_error)
                else:
                    self.warn(syntax_error)
                    return  # Don't try to continue

            # Reset the %Previous state if this is a new +Trigger.
            if cmd == '+':
                isThat = None

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
                            isThat = None

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
                            line += self.concat_modes.get(
                                local_options["concat"], ""
                            ) + lookahead
                        else:
                            break

            self.say("Command: " + cmd + "; line: " + line)

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
                            self.warn("Unsupported RiveScript version. We only support " + rs_version, filename, lineno)
                            return
                    except:
                        self.warn("Error parsing RiveScript version number: not a number", filename, lineno)
                    continue

                # All other types of defines require a variable and value name.
                if len(var) == 0:
                    self.warn("Undefined variable name", filename, lineno)
                    continue
                elif len(value) == 0:
                    self.warn("Undefined variable value", filename, lineno)
                    continue

                # Handle the rest of the types.
                if type == 'local':
                    # Local file-scoped parser options.
                    self.say("\tSet parser option " + var + " = " + value)
                    local_options[var] = value
                elif type == 'global':
                    # 'Global' variables
                    self.say("\tSet global " + var + " = " + value)

                    if value == '<undef>':
                        try:
                            del(ast["begin"]["global"][var])
                        except:
                            self.warn("Failed to delete missing global variable", filename, lineno)
                    else:
                        ast["begin"]["global"][var] = value

                    # Handle flipping debug and depth vars.
                    if var == 'debug':
                        if value.lower() == 'true':
                            value = True
                        else:
                            value = False
                    elif var == 'depth':
                        try:
                            value = int(value)
                        except:
                            self.warn("Failed to set 'depth' because the value isn't a number!", filename, lineno)
                    elif var == 'strict':
                        if value.lower() == 'true':
                            value = True
                        else:
                            value = False
                elif type == 'var':
                    # Bot variables
                    self.say("\tSet bot variable " + var + " = " + value)

                    if value == '<undef>':
                        try:
                            del(ast["begin"]["var"][var])
                        except:
                            self.warn("Failed to delete missing bot variable", filename, lineno)
                    else:
                        ast["begin"]["var"][var] = value
                elif type == 'array':
                    # Arrays
                    self.say("\tArray " + var + " = " + value)

                    if value == '<undef>':
                        try:
                            del(ast["begin"]["array"][var])
                        except:
                            self.warn("Failed to delete missing array", filename, lineno)
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

                    ast["begin"]["array"][var] = fields
                elif type == 'sub':
                    # Substitutions
                    self.say("\tSubstitution " + var + " => " + value)

                    if value == '<undef>':
                        try:
                            del(ast["begin"]["sub"][var])
                        except:
                            self.warn("Failed to delete missing substitution", filename, lineno)
                    else:
                        ast["begin"]["sub"][var] = value
                elif type == 'person':
                    # Person Substitutions
                    self.say("\tPerson Substitution " + var + " => " + value)

                    if value == '<undef>':
                        try:
                            del(ast["begin"]["person"][var])
                        except:
                            self.warn("Failed to delete missing person substitution", filename, lineno)
                    else:
                        ast["begin"]["person"][var] = value
                else:
                    self.warn("Unknown definition type '" + type + "'", filename, lineno)
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
                    self.say("\tFound the BEGIN block.")
                    type = 'topic'
                    name = '__begin__'
                if type == 'topic':
                    # Starting a new topic.
                    self.say("\tSet topic to " + name)
                    curtrig = None
                    topic  = name

                    # Initialize the topic tree.
                    self._init_topic(ast["topics"], topic)

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
                                    ast["topics"][name]["includes"][field] = 1
                                else:
                                    ast["topics"][name]["inherits"][field] = 1
                elif type == 'object':
                    # If a field was provided, it should be the programming
                    # language.
                    lang = None
                    if len(fields) > 0:
                        lang = fields[0].lower()

                    # Only try to parse a language we support.
                    curtrig = None
                    if lang is None:
                        self.warn("Trying to parse unknown programming language", filename, lineno)
                        lang = 'python'  # Assume it's Python.

                    # We have a handler, so start loading the code.
                    objname = name
                    objlang = lang
                    objbuf  = []
                    inobj   = True
                else:
                    self.warn("Unknown label type '" + type + "'", filename, lineno)
            elif cmd == '<':
                # < LABEL
                type = line

                if type == 'begin' or type == 'topic':
                    self.say("\tEnd topic label.")
                    topic = 'random'
                elif type == 'object':
                    self.say("\tEnd object label.")
                    inobj = False
            elif cmd == '+':
                # + TRIGGER
                self.say("\tTrigger pattern: " + line)

                # Initialize the topic tree.
                self._init_topic(ast["topics"], topic)
                curtrig = {
                    "trigger": line,
                    "reply": [],
                    "condition": [],
                    "redirect": None,
                    "previous": isThat,
                }
                ast["topics"][topic]["triggers"].append(curtrig)
            elif cmd == '-':
                # - REPLY
                if curtrig is None:
                    self.warn("Response found before trigger", filename, lineno)
                    continue

                self.say("\tResponse: " + line)
                curtrig["reply"].append(line.strip())
            elif cmd == '%':
                # % PREVIOUS
                pass  # This was handled above.
            elif cmd == '^':
                # ^ CONTINUE
                pass  # This was handled above.
            elif cmd == '@':
                # @ REDIRECT
                if curtrig is None:
                    self.warn("Redirect found before trigger", filename, lineno)
                    continue

                self.say("\tRedirect: " + line)
                curtrig["redirect"] = line.strip()
            elif cmd == '*':
                # * CONDITION
                if curtrig is None:
                    self.warn("Condition found before trigger", filename, lineno)
                    continue

                self.say("\tAdding condition: " + line)
                curtrig["condition"].append(line.strip())
            else:
                self.warn("Unrecognized command \"" + cmd + "\"", filename, lineno)
                continue

        return ast

    def check_syntax(self, cmd, line):
        """Syntax check a line of RiveScript code.

        Args:
            str cmd: The command symbol for the line of code, such as one
                of ``+``, ``-``, ``*``, ``>``, etc.
            str line: The remainder of the line of code, such as the text of
                a trigger or reply.

        Return:
            str: A string syntax error message or ``None`` if no errors.
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
                search = re.search(RE.name_syntax, line)
                if search:
                    return "Topics should be lowercased and contain only numbers and letters"
            elif parts[0] == "object":
                search = re.search(RE.obj_syntax, line) # Upper case is allowed
                if search:
                    return "Objects can only contain numbers and letters"
        elif cmd == '+' or cmd == '%' or cmd == '@':
            # + Trigger, % Previous, @ Redirect
            #   This one is strict. The triggers are to be run through the regexp engine,
            #   therefore it should be acceptable for the regexp engine.
            #   - Entirely lowercase
            #   - No symbols except: ( | ) [ ] * _ # @ { } < > =
            #   - All brackets should be matched
            #   - No empty option with pipe such as ||, [|, |], (|, |) and whitespace between
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

            # Check for empty pipe
            search = re.search(RE.empty_pipe, line)
            if search:
                return "Piped arrays can't include blank entries"

            # In UTF-8 mode, most symbols are allowed.
            if self.utf8:
                search = re.search(RE.utf8_trig, line)
                if search:
                    return "Triggers can't contain uppercase letters, backslashes or dots in UTF-8 mode."
            else:
                search = re.search(RE.trig_syntax, line)
                if search:
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

    def _init_topic(self, topics, name):
        """Initialize a Topic Tree data structure.

        Sets up the topic under ``ast.topics`` with all its relevant keys
        and sub-keys, etc.

        Args:
            topics (dict): A reference to the ``ast.topics``
            name (str): The name of the topic to initialize.

        Returns:
            None
        """
        if not name in topics:
            topics[name] = {
                "includes": {},
                "inherits": {},
                "triggers": [],
            }
