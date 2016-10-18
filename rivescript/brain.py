# RiveScript-Python
#
# This code is released under the MIT License.
# See the "LICENSE" file for more information.
#
# https://www.rivescript.com/

from __future__ import unicode_literals
from .regexp import RE
from .exceptions import (
    RiveScriptError, RepliesNotSortedError, NoDefaultRandomTopicError,
    DeepRecursionError, NoMatchError, NoReplyError, ObjectError,
    RS_ERR_OBJECT, RS_ERR_OBJECT_HANDLER, RS_ERR_OBJECT_MISSING
)
from . import python
from . import inheritance as inherit_utils
from . import utils
import random
import re
from six import text_type
import sys

class Brain(object):
    """The Brain class controls the actual reply fetching phase for RiveScript.

    Parameters:
        master (RiveScript): A reference to the parent RiveScript instance.
        strict (bool): Whether strict mode is enabled.
        utf8 (bool): Whether UTF-8 mode is enabled.
    """

    def __init__(self, master, strict=True, utf8=False):
        self.master = master
        self.strict = strict
        self.utf8   = utf8

        # Private variables only relevant to the reply-answering part of RiveScript.
        self._current_user = None

    # Proxy functions.
    def say(self, *args, **kwargs):
        self.master._say(*args, **kwargs)
    def warn(self, *args, **kwargs):
        self.master._warn(*args, **kwargs)

    def reply(self, user, msg, errors_as_replies=True):
        self.say("Get reply to [" + user + "] " + msg)

        # Store the current user in case an object macro needs it.
        self._current_user = user

        # Format their message.
        msg = self.format_message(msg)

        reply = ''

        # If the BEGIN block exists, consult it first.
        if "__begin__" in self.master._topics:
            try:
                begin = self._getreply(user, 'request', context='begin', ignore_object_errors=errors_as_replies)
            except RiveScriptError as e:
                if not errors_as_replies:
                    raise
                return e.error_message

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
            reply = self.process_tags(user, msg, reply, ignore_object_errors=errors_as_replies)
        else:
            # Just continue then.
            try:
                reply = self._getreply(user, msg, ignore_object_errors=errors_as_replies)
            except RiveScriptError as e:
                if not errors_as_replies:
                    raise
                reply = e.error_message

        # Save their reply history.
        history = self.master.get_uservar(user, "__history__")
        if type(history) is dict:
            oldInput = history["input"][:8]
            history["input"] = [msg]
            history["input"].extend(oldInput)
            oldReply = history["reply"][:8]
            history["reply"] = [reply]
            history["reply"].extend(oldReply)
            self.master.set_uservar(user, "__history__", history)

        # Unset the current user.
        self._current_user = None

        return reply

    def format_message(self, msg, botreply=False):
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
        msg = self.substitute(msg, "sub")

        # In UTF-8 mode, only strip metacharacters and HTML brackets
        # (to protect from obvious XSS attacks).
        if self.utf8:
            msg = re.sub(RE.utf8_meta, '', msg)
            msg = re.sub(self.master.unicode_punctuation, '', msg)

            # For the bot's reply, also strip common punctuation.
            if botreply:
                msg = re.sub(RE.utf8_punct, '', msg)
        else:
            # For everything else, strip all non-alphanumerics.
            msg = utils.strip_nasties(msg)

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
        if 'topics' not in self.master._sorted:
            raise RepliesNotSortedError("You must call sort_replies() once you are done loading RiveScript documents")

        # Initialize the user's profile?
        topic = self.master.get_uservar(user, "topic")
        if topic in [None, "undefined"]:
            topic = "random"
            self.master.set_uservar(user, "topic", topic)

        # Collect data on the user.
        stars     = []
        thatstars = []  # For %Previous's.
        reply     = ''

        # Avoid letting them fall into a missing topic.
        if topic not in self.master._topics:
            self.warn("User " + user + " was in an empty topic named '" + topic + "'")
            topic = "random"
            self.master.set_uservar(user, "topic", topic)

        # Avoid deep recursion.
        if step > self.master._depth:
            raise DeepRecursionError

        # Are we in the BEGIN statement?
        if context == 'begin':
            topic = '__begin__'

        # Initialize this user's history.
        history = self.master.get_uservar(user, "__history__")
        if type(history) is not dict or "input" not in history or "reply" not in history:
            history = self.default_history()
            self.master.set_uservar(user, "__history__", history)

        # More topic sanity checking.
        if topic not in self.master._topics:
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
            if topic in self.master._includes or topic in self.master._lineage:
                # Get all the topics!
                allTopics = inherit_utils.get_topic_tree(self.master, topic)

            # Scan them all!
            for top in allTopics:
                self.say("Checking topic " + top + " for any %Previous's.")
                if top in self.master._sorted["thats"]:
                    self.say("There is a %Previous in this topic!")

                    # Do we have history yet?
                    lastReply = history["reply"][0]

                    # Format the bot's last reply the same way as the human's.
                    lastReply = self.format_message(lastReply, botreply=True)
                    self.say("lastReply: " + lastReply)

                    # See if it's a match.
                    for trig in self.master._sorted["thats"][top]:
                        pattern = trig[0]
                        botside = self.reply_regexp(user, pattern)
                        self.say("Try to match lastReply (" + lastReply + ") to " + pattern)

                        # Match??
                        match = re.match(botside, lastReply)
                        if match:
                            # Huzzah! See if OUR message is right too.
                            self.say("Bot side matched!")
                            thatstars = match.groups()

                            # Compare the triggers to the user's message.
                            user_side = trig[1]
                            subtrig = self.reply_regexp(user, user_side["trigger"])
                            self.say("Now try to match " + msg + " to " + user_side["trigger"])

                            match = re.match(subtrig, msg)
                            if match:
                                self.say("Found a match!")
                                matched = trig[1]
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
            for trig in self.master._sorted["topics"][topic]:
                pattern = trig[0]

                # Process the triggers.
                regexp = self.reply_regexp(user, pattern)
                self.say("Try to match %r against %r (%r)" % (msg, pattern, regexp.pattern))

                # Python's regular expression engine is slow. Try a verbatim
                # match if this is an atomic trigger.
                isAtomic = utils.is_atomic(pattern)
                isMatch = False
                if isAtomic:
                    # Only look for exact matches, no sense running atomic triggers
                    # through the regexp engine.
                    if msg == pattern:
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
                    self.say("Found a match!")

                    matched = trig[1]
                    foundMatch = True
                    matchedTrigger = pattern
                    break

        # Store what trigger they matched on. If their matched trigger is None,
        # this will be too, which is great.
        self.master.set_uservar(user, "__lastmatch__", matchedTrigger)

        if matched:
            for nil in [1]:
                # See if there are any hard redirects.
                if matched["redirect"]:
                    self.say("Redirecting us to " + matched["redirect"])
                    redirect = self.process_tags(user, msg, matched["redirect"], stars, thatstars, step,
                                                  ignore_object_errors)
                    self.say("Pretend user said: " + redirect)
                    reply = self._getreply(user, redirect, step=(step + 1), ignore_object_errors=ignore_object_errors)
                    break

                # Check the conditionals.
                for con in matched["condition"]:
                    halves = re.split(RE.cond_split, con)
                    if halves and len(halves) == 2:
                        condition = re.match(RE.cond_parse, halves[0])
                        if condition:
                            left     = condition.group(1)
                            eq       = condition.group(2)
                            right    = condition.group(3)
                            potreply = halves[1]
                            self.say("Left: " + left + "; eq: " + eq + "; right: " + right + " => " + potreply)

                            # Process tags all around.
                            left  = self.process_tags(user, msg, left, stars, thatstars, step, ignore_object_errors)
                            right = self.process_tags(user, msg, right, stars, thatstars, step, ignore_object_errors)

                            # Defaults?
                            if len(left) == 0:
                                left = 'undefined'
                            if len(right) == 0:
                                right = 'undefined'

                            self.say("Check if " + left + " " + eq + " " + right)

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
                                    self.warn("Failed to evaluate numeric condition!")

                            # How truthful?
                            if passed:
                                reply = potreply
                                break

                # Have our reply yet?
                if len(reply) > 0:
                    break

                # Process weights in the replies.
                bucket = []
                for text in matched["reply"]:
                    weight = 1
                    match  = re.match(RE.weight, text)
                    if match:
                        weight = int(match.group(1))
                        if weight <= 0:
                            self.warn("Can't have a weight <= 0!")
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

        self.say("Reply: " + reply)

        # Process tags for the BEGIN block.
        if context == "begin":
            # BEGIN blocks can only set topics and uservars. The rest happen
            # later!
            reTopic = re.findall(RE.topic_tag, reply)
            for match in reTopic:
                self.say("Setting user's topic to " + match)
                self.master.set_uservar(user, "topic", match)
                reply = reply.replace('{{topic={match}}}'.format(match=match), '')

            reSet = re.findall(RE.set_tag, reply)
            for match in reSet:
                self.say("Set uservar " + str(match[0]) + "=" + str(match[1]))
                self.master.set_uservar(user, match[0], match[1])
                reply = reply.replace('<set {key}={value}>'.format(key=match[0], value=match[1]), '')
        else:
            # Process more tags if not in BEGIN.
            reply = self.process_tags(user, msg, reply, stars, thatstars, step, ignore_object_errors)

        return reply

    def reply_regexp(self, user, regexp):
        """Prepares a trigger for the regular expression engine.

        :param str user: The user ID invoking a reply.
        :param str regexp: The original trigger text to be turned into a regexp.

        :return regexp: The final regexp object."""

        if regexp in self.master._regexc["trigger"]:
            # Already compiled this one!
            return self.master._regexc["trigger"][regexp]

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
            pipes = pipes.replace(r'(.+?)', r'(?:.+?)')
            pipes = pipes.replace(r'(\d+?)', r'(?:\d+?)')
            pipes = pipes.replace(r'([A-Za-z]+?)', r'(?:[A-Za-z]+?)')

            regexp = re.sub(r'\s*\[' + re.escape(match) + '\]\s*',
                '(?:' + pipes + r'|(?:\\s|\\b))', regexp)

        # _ wildcards can't match numbers!
        regexp = re.sub(RE.literal_w, r'[A-Za-z]', regexp)

        # Filter in arrays.
        arrays = re.findall(RE.array, regexp)
        for array in arrays:
            rep = ''
            if array in self.master._array:
                rep = r'(?:' + '|'.join(self.expand_array(array)) + ')'
            regexp = re.sub(r'\@' + re.escape(array) + r'\b', rep, regexp)

        # Filter in bot variables.
        bvars = re.findall(RE.bot_tag, regexp)
        for var in bvars:
            rep = ''
            if var in self.master._var:
                rep = utils.strip_nasties(self.master._var[var])
            regexp = regexp.replace('<bot {var}>'.format(var=var), rep)

        # Filter in user variables.
        uvars = re.findall(RE.get_tag, regexp)
        for var in uvars:
            rep = ''
            value = self.master.get_uservar(user, var)
            if value not in [None, "undefined"]:
                rep = utils.strip_nasties(value)
            regexp = regexp.replace('<get {var}>'.format(var=var), rep)

        # Filter in <input> and <reply> tags. This is a slow process, so only
        # do it if we have to!
        if '<input' in regexp or '<reply' in regexp:
            history = self.master.get_uservar(user, "__history__")
            for type in ['input', 'reply']:
                tags = re.findall(r'<' + type + r'([0-9])>', regexp)
                for index in tags:
                    rep = self.format_message(history[type][int(index) - 1])
                    regexp = regexp.replace('<{type}{index}>'.format(type=type, index=index), rep)
                regexp = regexp.replace('<{type}>'.format(type=type),
                                        self.format_message(history[type][0]))
                # TODO: the Perl version doesn't do just <input>/<reply> in trigs!

        return re.compile(r'^' + regexp + r'$')

    def do_expand_array(self, array_name, depth=0):
        """Do recurrent array expansion, returning a set of keywords.

        Exception is thrown when there are cyclical dependencies between
        arrays or if the ``@array`` name references an undefined array.

        :param str array_name: The name of the array to expand.
        :param int depth: The recursion depth counter.

        :return set: The final set of array entries.
        """
        if depth > self.master._depth:
            raise Exception("deep recursion detected")
        if not array_name in self.master._array:
            raise Exception("array '%s' not defined" % (array_name))
        ret = list(self.master._array[array_name])
        for array in self.master._array[array_name]:
            if array.startswith('@'):
                ret.remove(array)
                expanded = self.do_expand_array(array[1:], depth+1)
                ret.extend(expanded)

        return set(ret)

    def expand_array(self, array_name):
        """Expand variables and return a set of keywords.

        :param str array_name: The name of the array to expand.

        :return list: The final array contents.

        Warning is issued when exceptions occur."""
        ret = self.master._array[array_name] if array_name in self.master._array else []
        try:
            ret = self.do_expand_array(array_name)
        except Exception as e:
            self.warn("Error expanding array '%s': %s" % (array_name, str(e)))
        return ret

    def process_tags(self, user, msg, reply, st=[], bst=[], depth=0, ignore_object_errors=True):
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
        history = self.master.get_uservar(user, "__history__")
        if type(history) is not dict:
            history = self.default_history()
        reply = reply.replace('<input>', history['input'][0])
        reply = reply.replace('<reply>', history['reply'][0])
        reInput = re.findall(RE.input_tags, reply)
        for match in reInput:
            reply = reply.replace('<input{match}>'.format(match=match),
                                  history['input'][int(match) - 1])
        reReply = re.findall(RE.reply_tags, reply)
        for match in reReply:
            reply = reply.replace('<reply{match}>'.format(match=match),
                                  history['reply'][int(match) - 1])

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
                    output = self.substitute(match, "person")
                else:
                    output = utils.string_format(match, item)
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
                target = self.master._var if tag == "bot" else self.master._global
                if "=" in data:
                    # Setting a bot/env variable.
                    parts = data.split("=")
                    self.say("Set " + tag + " variable " + text_type(parts[0]) + "=" + text_type(parts[1]))
                    target[parts[0]] = parts[1]
                else:
                    # Getting a bot/env variable.
                    insert = target.get(data, "undefined")
            elif tag == "set":
                # <set> user vars.
                parts = data.split("=")
                self.say("Set uservar " + text_type(parts[0]) + "=" + text_type(parts[1]))
                self.master.set_uservar(user, parts[0], parts[1])
            elif tag in ["add", "sub", "mult", "div"]:
                # Math operator tags.
                parts = data.split("=")
                var   = parts[0]
                value = parts[1]
                curv  = self.master.get_uservar(user, var)

                # Sanity check the value.
                try:
                    value = int(value)
                    if curv in [None, "undefined"]:
                        # Initialize it.
                        curv = 0
                except:
                    insert = "[ERR: Math can't '{}' non-numeric value '{}']".format(tag, value)

                # Attempt the operation.
                try:
                    orig = int(curv)
                    new  = 0
                    if tag == "add":
                        new = orig + value
                    elif tag == "sub":
                        new = orig - value
                    elif tag == "mult":
                        new = orig * value
                    elif tag == "div":
                        new = orig / value
                    self.master.set_uservar(user, var, new)
                except:
                    insert = "[ERR: Math couldn't '{}' to value '{}']".format(tag, curv)
            elif tag == "get":
                insert = self.master.get_uservar(user, data)
            else:
                # Unrecognized tag.
                insert = "\x00{}\x01".format(match)

            reply = reply.replace("<{}>".format(match), text_type(insert))

        # Restore unrecognized tags.
        reply = reply.replace("\x00", "<").replace("\x01", ">")

        # Streaming code. DEPRECATED!
        if '{!' in reply:
            self._warn("Use of the {!...} tag is deprecated and not supported here.")

        # Topic setter.
        reTopic = re.findall(RE.topic_tag, reply)
        for match in reTopic:
            self.say("Setting user's topic to " + match)
            self.master.set_uservar(user, "topic", match)
            reply = reply.replace('{{topic={match}}}'.format(match=match), '')

        # Inline redirecter.
        reRedir = re.findall(RE.redir_tag, reply)
        for match in reRedir:
            self.say("Redirect to " + match)
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
            if obj in self.master._objlangs:
                # We do, but do we have a handler for that language?
                lang = self.master._objlangs[obj]
                if lang in self.master._handlers:
                    # We do.
                    try:
                        output = self.master._handlers[lang].call(self.master, obj, user, args)
                    except python.PythonObjectError as e:
                        self.warn(str(e))
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

    def substitute(self, msg, kind):
        """Run a kind of substitution on a message.

        :param str msg: The message to run substitutions against.
        :param str kind: The kind of substitution to run,
            one of ``subs`` or ``person``.
        """

        # Safety checking.
        if 'lists' not in self.master._sorted:
            raise RepliesNotSortedError("You must call sort_replies() once you are done loading RiveScript documents")
        if kind not in self.master._sorted["lists"]:
            raise RepliesNotSortedError("You must call sort_replies() once you are done loading RiveScript documents")

        # Get the substitution map.
        subs = None
        if kind == 'sub':
            subs = self.master._sub
        else:
            subs = self.master._person

        # Make placeholders each time we substitute something.
        ph = []
        i  = 0

        for pattern in self.master._sorted["lists"][kind]:
            result = subs[pattern]

            # Make a placeholder.
            ph.append(result)
            placeholder = "\x00%d\x00" % i
            i += 1

            cache = self.master._regexc[kind][pattern]
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

    def default_history(self):
        return {
            "input": ["undefined"] * 9,
            "reply": ["undefined"] * 9,
        }
