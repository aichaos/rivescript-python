# RiveScript-Python
#
# This code is released under the MIT License.
# See the "LICENSE" file for more information.
#
# https://www.rivescript.com/

from .regexp import RE
from . import utils
import re

def sort_trigger_set(triggers, exclude_previous=True, say=None):
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

    Arguments:
        triggers ([]str): Array of triggers to sort.
        exclude_previous (bool): Create a sort buffer for 'previous' triggers.
        say (function): A reference to ``RiveScript._say()`` or provide your
            own function.
    """
    if say is None:
        say = lambda x: x

    # KEEP IN MIND: the `triggers` array is composed of array elements of the form
    # ["trigger text", pointer to trigger data]
    # So this code will use e.g. `trig[0]` when referring to the trigger text.

    # Create a priority map.
    prior = {
        0: []  # Default priority=0
    }

    for trig in triggers:
        if exclude_previous and trig[1]["previous"]:
            continue

        match, weight = re.search(RE.weight, trig[0]), 0
        if match:
            weight = int(match.group(1))
        if weight not in prior:
            prior[weight] = []

        prior[weight].append(trig)

    # Keep a running list of sorted triggers for this topic.
    running = []

    # Sort them by priority.
    for p in sorted(prior.keys(), reverse=True):
        say("\tSorting triggers with priority " + str(p))

        # So, some of these triggers may include {inherits} tags, if they
        # came form a topic which inherits another topic. Lower inherits
        # values mean higher priority on the stack.
        inherits = -1          # -1 means no {inherits} tag
        highest_inherits = -1  # highest inheritance number seen

        # Loop through and categorize these triggers.
        track = {
            inherits: init_sort_track()
        }

        for trig in prior[p]:
            pattern = trig[0]
            say("\t\tLooking at trigger: " + pattern)

            # See if it has an inherits tag.
            match = re.search(RE.inherit, pattern)
            if match:
                inherits = int(match.group(1))
                if inherits > highest_inherits:
                    highest_inherits = inherits
                say("\t\t\tTrigger belongs to a topic which inherits other topics: level=" + str(inherits))
                pattern = re.sub(RE.inherit, "", pattern)
                trig[0] = pattern
            else:
                inherits = -1

            # If this is the first time we've seen this inheritance level,
            # initialize its track structure.
            if inherits not in track:
                track[inherits] = init_sort_track()

            # Start inspecting the trigger's contents.
            if '_' in pattern:
                # Alphabetic wildcard included.
                cnt = utils.word_count(pattern)
                say("\t\t\tHas a _ wildcard with " + str(cnt) + " words.")
                if cnt > 1:
                    if cnt not in track[inherits]['alpha']:
                        track[inherits]['alpha'][cnt] = []
                    track[inherits]['alpha'][cnt].append(trig)
                else:
                    track[inherits]['under'].append(trig)
            elif '#' in pattern:
                # Numeric wildcard included.
                cnt = utils.word_count(pattern)
                say("\t\t\tHas a # wildcard with " + str(cnt) + " words.")
                if cnt > 1:
                    if cnt not in track[inherits]['number']:
                        track[inherits]['number'][cnt] = []
                    track[inherits]['number'][cnt].append(trig)
                else:
                    track[inherits]['pound'].append(trig)
            elif '*' in pattern:
                # Wildcard included.
                cnt = utils.word_count(pattern)
                say("\t\t\tHas a * wildcard with " + str(cnt) + " words.")
                if cnt > 1:
                    if cnt not in track[inherits]['wild']:
                        track[inherits]['wild'][cnt] = []
                    track[inherits]['wild'][cnt].append(trig)
                else:
                    track[inherits]['star'].append(trig)
            elif '[' in pattern:
                # Optionals included.
                cnt = utils.word_count(pattern)
                say("\t\t\tHas optionals and " + str(cnt) + " words.")
                if cnt not in track[inherits]['option']:
                    track[inherits]['option'][cnt] = []
                track[inherits]['option'][cnt].append(trig)
            else:
                # Totally atomic.
                cnt = utils.word_count(pattern)
                say("\t\t\tTotally atomic and " + str(cnt) + " words.")
                if cnt not in track[inherits]['atomic']:
                    track[inherits]['atomic'][cnt] = []
                track[inherits]['atomic'][cnt].append(trig)

        # Move the no-{inherits} triggers to the bottom of the stack.
        track[highest_inherits + 1] = track[-1]
        del(track[-1])

        # Add this group to the sort list.
        for ip in sorted(track.keys()):
            say("ip=" + str(ip))
            for kind in ['atomic', 'option', 'alpha', 'number', 'wild']:
                for wordcnt in sorted(track[ip][kind], reverse=True):
                    # Triggers with a matching word count should be sorted
                    # by length, descending.
                    running.extend(sorted(track[ip][kind][wordcnt], key=len, reverse=True))
            running.extend(sorted(track[ip]['under'], key=len, reverse=True))
            running.extend(sorted(track[ip]['pound'], key=len, reverse=True))
            running.extend(sorted(track[ip]['star'], key=len, reverse=True))
    return running

def sort_list(items):
    """Sort a simple list by number of words and length."""

    # Track by number of words.
    track = {}

    def by_length(word1, word2):
        return len(word2) - len(word1)

    # Loop through each item.
    for item in items:
        # Count the words.
        cword = utils.word_count(item, all=True)
        if cword not in track:
            track[cword] = []
        track[cword].append(item)

    # Sort them.
    output = []
    for count in sorted(track.keys(), reverse=True):
        sort = sorted(track[count], key=len, reverse=True)
        output.extend(sort)

    return output

def init_sort_track():
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
