#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import unicode_literals, absolute_import

from rivescript.exceptions import RS_ERR_MATCH
from .config import RiveScriptTestCase

class SortingTriggersTest(RiveScriptTestCase):
    """Topic tests."""

    def test_sorting_triggers(self):
        self.new("""
            + * you *
            - 1

            + * are *
            - 2

            + * how are you *
            - 3

            + * hallo ween *
            - 4

            + (hi|hii)
            - 5

            + hello
            - 6 

            + hey [man]
            - 7

            + good morning
            - 8

            + *
            - 9

            + hel lo
            - 10

            + hi *
            - 11

            + hi [*]
            - 12
        """)
        
        sorted_triggers =  {trig[0]:position for position, trig in enumerate(self.rs._brain.master._sorted["topics"]['random'])}

        # 1) Atomic is first matched. 
        self.assertLess(sorted_triggers['hello'],sorted_triggers['hey [man]'])

        # 2) Sorted by number of words 
        self.assertLess(sorted_triggers['hel lo'],sorted_triggers['hello'])
        self.assertLess(sorted_triggers['* hallo ween *'],sorted_triggers['* are *'])

        # 3) Sorted by length by characters 
        self.assertLess(sorted_triggers['good morning'],sorted_triggers['hel lo'])

        # 4) Sorted by alphabetical order
        self.assertLess(sorted_triggers['* are *'],sorted_triggers['* you *'])

        # 5) Sorted by number of wildcard triggers 
        self.assertLess(sorted_triggers['hi *'],sorted_triggers['* you *'])

        # 6) The `super catch all` (only single star `*`) should be least priority
        self.assertEqual(sorted_triggers['*'],max(sorted_triggers.values()))
        self.assertLess(sorted_triggers['hi [*]'],sorted_triggers['*']) # another check but will be covered by max check above


