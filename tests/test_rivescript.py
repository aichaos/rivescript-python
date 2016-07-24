#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import unicode_literals, absolute_import

import json
import re
import unittest
from collections import OrderedDict

from rivescript.rivescript import RS_ERR_MATCH

from .config import RiveScriptTestCase

class APITest(RiveScriptTestCase):
    """Miscellaneous API tests."""

    def test_set_uservars(self):
        self.new("""
            + who am i
            - You are <get name>, seeker!

            + how old am i
            - You are <get age> years old.
        """)

        # Test the base case, with no vars set.
        self.reply("Who am I?", "You are undefined, seeker!")
        self.reply("How old am I?", "You are undefined years old.")

        # Set setting one variable at a time.
        self.rs.set_uservar("localuser", "name", "Alice")
        self.rs.set_uservar("localuser", "age", "10")
        self.reply("Who am I?", "You are Alice, seeker!")
        self.reply("How old am I?", "You are 10 years old.")

        # Test setting a dict of variables for one user.
        self.rs.set_uservars("localuser", {
            "name": "Eliza",
            "age": "20",
        })
        self.reply("Who am I?", "You are Eliza, seeker!")
        self.reply("How old am I?", "You are 20 years old.")

        # Test setting a partial dict which only updates named keys.
        self.rs.set_uservars("localuser", dict(name="UltraHAL"))
        self.reply("Who am I?", "You are UltraHAL, seeker!")
        self.reply("How old am I?", "You are 20 years old.")

        # Test setting a dict of many users to many keys.
        self.rs.set_uservars({
            "localuser": {
                "age": "22",
            },
            "testuser": {
                "name": "Bob",
            }
        })
        self.reply("Who am I?", "You are UltraHAL, seeker!")
        self.reply("How old am I?", "You are 22 years old.")
        self.assertEqual(self.rs.get_uservar("testuser", "name"), "Bob")
        self.assertEqual(self.rs.get_uservar("testuser", "age"), "undefined")

        # Non-existing users return None, not "undefined"
        self.assertEqual(self.rs.get_uservar("fake", "name"), None)

        # Test setting vars from exported vars.
        exported = self.rs.get_uservars("localuser")
        self.assertEqual(self.rs.set_uservars("localuser", exported), None)

        # Test setting vars from JSON.
        self.assertEqual(self.rs.set_uservars("localuser",
            json.loads('{"gender": "ambiguous"}')), None)

        # Test setting user variables for users that don't exist yet.
        self.assertEqual(self.rs.set_uservars("newbie", {"name": "Newbie"}), None)

        # Test calling with (str, None)
        with self.assertRaises(TypeError):
            self.rs.set_uservars("alice")

        # Test calling with (str, str)
        with self.assertRaises(TypeError):
            self.rs.set_uservars("alice", "name")

        # Test calling with (dict, dict)
        with self.assertRaises(TypeError):
            self.rs.set_uservars({"localuser": "hi"}, {"name": "Alice"})

        # Test calling it in many-users mode, where one of the users isn't
        # a dict.
        with self.assertRaises(TypeError):
            self.rs.set_uservars({
                "localuser": {
                    "name": "Mary",
                },
                "testuser": "not a dict",
            })

        # Test calling with dict-like objects.
        with self.assertRaises(TypeError):
            self.rs.set_uservars("localuser", OrderedDict(name="Alice"))

        # But dict-like objects can be cast as dicts.
        testdict = OrderedDict(name="Joe")
        self.assertEqual(self.rs.set_uservars("localuser", dict(testdict)), None)

if __name__ == "__main__":
    unittest.main()
