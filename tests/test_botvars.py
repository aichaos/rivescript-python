#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import unicode_literals, absolute_import

from .config import RiveScriptTestCase

class BotvarTests(RiveScriptTestCase):
    """Test bot variables."""

    def test_bot_variables(self):
        self.new("""
            ! var name = Aiden
            ! var age = 5

            + what is your name
            - My name is <bot name>.

            + how old are you
            - I am <bot age>.

            + what are you
            - I'm <bot gender>.

            + happy birthday
            - <bot age=6>Thanks!

            + who is your master
            - My master is <bot master>.
        """)
        self.rs.set_variable("master", "kirsle")

        self.reply("What is your name?", "My name is Aiden.")
        self.reply("How old are you?", "I am 5.")
        self.reply("What are you?", "I'm undefined.")
        self.reply("Happy birthday!", "Thanks!")
        self.reply("How old are you?", "I am 6.")
        self.reply("Who is your master?", "My master is kirsle.")

        self.assertEqual(self.rs.get_variable("age"), "6")
        self.assertEqual(self.rs.get_variable("master"), "kirsle")
        self.assertEqual(self.rs.get_variable("fake"), "undefined")

    def test_global_variables(self):
        self.new("""
            ! global debug = false

            + debug mode
            - Debug mode is: <env debug>

            + set debug mode *
            - <env debug=<star>>Switched to <star>.

            + are you testing
            - Testing: <env testing>
        """)
        self.rs.set_global("testing", "true")

        self.reply("Debug mode.", "Debug mode is: false")
        self.reply("Set debug mode true", "Switched to true.")
        self.reply("Debug mode?", "Debug mode is: true")
        self.reply("Are you testing?", "Testing: true")

        self.assertEqual(self.rs.get_global("debug"), "true")
        self.assertEqual(self.rs.get_global("testing"), "true")
        self.assertEqual(self.rs.get_global("fake"), "undefined")
