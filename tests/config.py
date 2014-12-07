#!/usr/bin/env python

"""Utility functions for the unit tests."""

import unittest
from rivescript import RiveScript

class RiveScriptTestCase(unittest.TestCase):
    """Base class for all RiveScript test cases, with helper functions."""

    def setUp(self, **kwargs):
        self.rs = None # Local RiveScript bot object
        self.username = "localuser"


    def tearDown(self):
        pass


    def new(self, code, **kwargs):
        """Make a bot and stream in the code."""
        self.rs = RiveScript(**kwargs)
        self.extend(code)


    def extend(self, code):
        """Stream code into the bot."""
        self.rs.stream(code)
        self.rs.sort_replies()


    def reply(self, message, expected):
        """Test that the user's message gets the expected response."""
        reply = self.rs.reply(self.username, message)
        self.assertEqual(reply, expected)


    def uservar(self, var, expected):
        """Test the value of a user variable."""
        value = self.rs.get_uservar(self.username, var)
        self.assertEqual(value, expected)
