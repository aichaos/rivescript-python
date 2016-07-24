#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import unicode_literals, absolute_import

from .config import RiveScriptTestCase

class ReplyTests(RiveScriptTestCase):
    """Response tests."""

    def test_previous(self):
        self.new("""
            ! sub who's  = who is
            ! sub it's   = it is
            ! sub didn't = did not

            + knock knock
            - Who's there?

            + *
            % who is there
            - <sentence> who?

            + *
            % * who
            - Haha! <sentence>!

            + *
            - I don't know.
        """)
        self.reply("knock knock", "Who's there?")
        self.reply("Canoe", "Canoe who?")
        self.reply("Canoe help me with my homework?", "Haha! Canoe help me with my homework!")
        self.reply("hello", "I don't know.")

    def test_continuations(self):
        self.new("""
            + tell me a poem
            - There once was a man named Tim,\\s
            ^ who never quite learned how to swim.\\s
            ^ He fell off a dock, and sank like a rock,\\s
            ^ and that was the end of him.
        """)
        self.reply("Tell me a poem.",
            "There once was a man named Tim, " \
            + "who never quite learned how to swim. " \
            + "He fell off a dock, and sank like a rock, " \
            + "and that was the end of him.")

    def test_redirects(self):
        self.new("""
            + hello
            - Hi there!

            + hey
            @ hello

            + hi there
            - {@hello}
        """)
        for greeting in ["hello", "hey", "hi there"]:
            self.reply(greeting, "Hi there!")

    def test_conditionals(self):
        self.new("""
            + i am # years old
            - <set age=<star>>OK.

            + what can i do
            * <get age> == undefined => I don't know.
            * <get age> >  25 => Anything you want.
            * <get age> == 25 => Rent a car for cheap.
            * <get age> >= 21 => Drink.
            * <get age> >= 18 => Vote.
            * <get age> <  18 => Not much of anything.

            + am i your master
            * <get master> == true => Yes.
            - No.
        """)
        age_q = "What can I do?"
        self.reply(age_q, "I don't know.")

        ages = {
            '16' : "Not much of anything.",
            '18' : "Vote.",
            '20' : "Vote.",
            '22' : "Drink.",
            '24' : "Drink.",
            '25' : "Rent a car for cheap.",
            '27' : "Anything you want.",
        }
        for age in sorted(ages.keys()):
            self.reply("I am {} years old.".format(age), "OK.")
            self.reply(age_q, ages[age])

        self.reply("Am I your master?", "No.")
        self.rs.set_uservar(self.username, "master", "true")
        self.reply("Am I your master?", "Yes.")

    def test_embedded_tags(self):
        self.new("""
            + my name is *
            * <get name> != undefined => <set oldname=<get name>>I thought\s
              ^ your name was <get oldname>?
              ^ <set name=<formal>>
            - <set name=<formal>>OK.

            + what is my name
            - Your name is <get name>, right?

            + html test
            - <set name=<b>Name</b>>This has some non-RS <em>tags</em> in it.
        """)
        self.reply("What is my name?", "Your name is undefined, right?")
        self.reply("My name is Alice", "OK.")
        self.reply("My name is Bob.", "I thought your name was Alice?")
        self.reply("What is my name?", "Your name is Bob, right?")
        self.reply("HTML Test", "This has some non-RS <em>tags</em> in it.")
