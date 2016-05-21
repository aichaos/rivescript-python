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

"""Exception classes for RiveScript."""

# Exportable constants.
RS_ERR_MATCH = "[ERR: No reply matched]"
RS_ERR_REPLY = "[ERR: No reply found]"
RS_ERR_DEEP_RECURSION = "[ERR: Deep recursion detected]"
RS_ERR_OBJECT = "[ERR: Error when executing Python object]"
RS_ERR_OBJECT_HANDLER = "[ERR: No Object Handler]"
RS_ERR_OBJECT_MISSING = "[ERR: Object Not Found]"

class RiveScriptError(Exception):
    """RiveScript base exception class."""
    def __init__(self, error_message=None):
        super(RiveScriptError, self).__init__(error_message)
        self.error_message = error_message


class NoMatchError(RiveScriptError):
    """No reply could be matched.

    This means that no trigger was a match for the user's message. To avoid
    this error, add a trigger that only consists of a wildcard::

        + *
        - I do not know how to reply to that.

    The lone-wildcard trigger acts as a catch-all fallback trigger and will
    ensure that every message the user could send will match at least one
    trigger.

    The text version is ``[ERR: No reply matched]``
    """
    def __init__(self):
        super(NoMatchError, self).__init__(RS_ERR_MATCH)


class NoReplyError(RiveScriptError):
    """No reply could be found.

    This means that the user's message matched a trigger, but the trigger
    didn't yield any response for the user. For example, if a trigger was
    followed only by ``*Conditions`` and none of them were true and there were
    no normal replies to fall back on, this error can come up.

    To avoid this error, always make sure you have at least one ``-Reply``
    for every trigger.

    The text version is ``[ERR: No reply found]``.
    """
    def __init__(self):
        super(NoReplyError, self).__init__(RS_ERR_REPLY)


class ObjectError(RiveScriptError):
    """An error occurred when executing a Python object macro.

    This will usually be some kind of run-time error, like a
    ``ZeroDivisionError`` or ``IndexError`` for example.

    The text version is ``[ERR: Error when executing Python object]``
    """
    def __init__(self, error_message=RS_ERR_OBJECT):
        super(ObjectError, self).__init__(error_message)


class DeepRecursionError(RiveScriptError):
    """A deep recursion condition was detected and a reply can't be given.

    This error can occur when you have triggers that redirect to each other
    in a circle, for example::

        + one
        @ two

        + two
        @ one

    By default, RiveScript will only recursively look for a trigger up to
    50 levels deep before giving up. This should be a large enough window for
    most use cases, but if you need to increase this limit you can do so by
    setting a higher value for the ``depth`` parameter to the constructor or
    changing it in your RiveScript source code, for example::

        ! global depth = 75

    The text version is ``[ERR: Deep recursion detected]``
    """
    def __init__(self):
        super(DeepRecursionError, self).__init__(RS_ERR_DEEP_RECURSION)


class NoDefaultRandomTopicError(Exception):
    """No default topic could be found.

    This is a critical error and usually means no replies were loaded into the
    bot. Very unlikely is it the case that all replies belong to other topics
    than the default (``random``)."""
    pass


class RepliesNotSortedError(Exception):
    """You attempted to get a reply before sorting the triggers.

    You should call ``sort_replies()`` after loading your RiveScript code and
    before calling ``reply()`` to look up a reply.
    """
    pass
