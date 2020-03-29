# RiveScript-Python
#
# This code is released under the MIT License.
# See the "LICENSE" file for more information.
#
# https://www.rivescript.com/

from __future__ import unicode_literals
from .regexp import RE
from . import utils
import re
from operator import attrgetter
import sys


class TriggerObj(object):
    """An object represent trigger for ease of sorting.

    In RiveScript sorting rule, some of sorting criteria are ascending for example alphabetical or inherit whereas other
    criteria are descending order for example word counts. In Python multiple level sort, the sort direction set by
    parameter `reverse` is applied to all criteria. So in our implementation, some parameters are set to negative to
    keep search direction consistent among all criteria.

        Parameters:
            pattern: Trigger pattern in string format i.e. "* hey [man]"
            index: Unique positional index of the object in the original list
            weight: Pattern weight ``{weight}``
            inherit: Pattern inherit level, extracted from i.e. "{inherit=1}hi"

        Computed:
            wordcount: Negative length of pattern by wordcount
            len: Negative length of pattern by character count
            star: Boolean - has wildcards (``*``), excluding alphabetical wildcards, and numeric wildcards
            pound: Boolean - has numeric wildcards (``#``)
            under: Boolean - has alphabetical wildcards (``_``)
            option: Boolean - has optional tags ("[man]" in "hey [man]"), assume that the template is properly formatted
            is_empty: Boolean variable indicating whether the trigger has non-zero wordcount
        """

    def __init__(self, pattern, index, weight, inherit = sys.maxsize):
        self.alphabet = pattern  # Sort according to alphabet order i.e. haha < hihi
        self.index = index  # For rearrange items in the sorted array
        self.weight = - weight  # Negative weight to place i.e. -100 < 0
        self.inherit = inherit  # Low inherit takes precedence i.e. 0 < 1
        self.wordcount = - utils.word_count(pattern)  # Length -2 < -1. Use `utils` for counting choice of wildcards
        self.len    = -len(self.alphabet)  # Length -10 < -5
        pattern_set = set(pattern)
        self.star   = '*' in pattern_set  # Has wildcards 0 < 1
        self.pound  = '#' in pattern_set  # Has numeric wildcards 0 < 1
        self.under  = '_' in pattern_set  # Has alpha wildcards 0 < 1
        self.option = '[' in pattern_set  # Has optionals 0 < 1
        #self.star   = self.alphabet.count('*')  # Number of wildcards 0 < 1
        #self.star   = self.alphabet.startswith('* ') + self.alphabet.count(' * ') + self.alphabet.endswith(' *') + \
                #self.alphabet.startswith('[*] ') + self.alphabet.endswith(' [*]') + \
                #(self.alphabet == '*') + (self.alphabet == '[*]')  # Number of wildcards 0 < 1
        #self.pound  = self.alphabet.count('#')  # Number of numeric wildcards 0 < 1
        #self.under  = self.alphabet.count('_')  # Number of alphabetical wildcards 0 < 1
        #self.option = self.alphabet.count('[') + self.alphabet.count('(')  # Number of option 0 < 1
        #self.option = self.alphabet.count('[') - self.alphabet.count('[*') + self.alphabet.count('(')  # Number of option 0 < 1
        self.is_empty = self.wordcount == 0  # Triggers with words precede triggers with no words, False < True


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

    # Create a list of trigger objects map.
    trigger_object_list = []
    for index, trig in enumerate(triggers):

        if exclude_previous and trig[1]["previous"]:
            continue

        pattern = trig[0]  # Extract only the text of the trigger, with possible tag of inherit

        # See if it has a weight tag
        match, weight = re.search(RE.weight, trig[0]), 0
        if match:  # Value of math is not None if there is a match.
            weight = int(match.group(1))  # Get the weight from the tag ``{weight}``

        # See if it has an inherits tag.
        match = re.search(RE.inherit, pattern)
        if match:
            inherit = int(match.group(1))  # Get inherit value from the tag ``{inherit}``
            say("\t\t\tTrigger belongs to a topic which inherits other topics: level=" + str(inherit))
            triggers[index][0] = pattern = re.sub(RE.inherit, "", pattern)  # Remove the inherit tag if any
        else:
            inherit = sys.maxsize  # If not found any inherit, set it to the maximum value, to place it last in the sort

        trigger_object_list.append(TriggerObj(pattern, index, weight, inherit))

    # Priority order of sorting criteria:
    # weight, inherit, is_empty, star, pound, under, option, wordcount, len, alphabet
    sorted_list = sorted(trigger_object_list,
                         key=attrgetter('weight', 'inherit', 'is_empty', 'star', 'pound',
                                        'under', 'option', 'wordcount', 'len', 'alphabet'))
    return [triggers[item.index] for item in sorted_list]

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
