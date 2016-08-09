# RiveScript-Python
#
# This code is released under the MIT License.
# See the "LICENSE" file for more information.
#
# https://www.rivescript.com/

from __future__ import unicode_literals
from .regexp import RE
import re
import string

def word_count(trigger, all=False):
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

def is_atomic(trigger):
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
    special = ['*', '#', '_', '(', '[', '<', '{', '@']
    for char in special:
        if char in trigger:
            return False

    return True

def strip_nasties(s):
    """Formats a string for ASCII regex matching."""
    s = re.sub(RE.nasties, '', s)
    return s

def string_format(msg, method):
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
