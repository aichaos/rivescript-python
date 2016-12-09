#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import unicode_literals, absolute_import

from rivescript.sessions import NullSessionStorage
from .config import RiveScriptTestCase

class SessionTests(RiveScriptTestCase):
    """Test session handlers."""

    common_session_test = """
        + my name is *
        - <set name=<formal>>Nice to meet you, <get name>.

        + who am i
        - Aren't you <get name>?

        + what did i just say
        - You just said: <input1>

        + what did you just say
        - I just said: <reply1>

        + i hate you
        - How mean!{topic=apology}

        > topic apology
            + *
            - Nope, I'm mad at you.
        < topic
    """

    def test_null_session(self):
        """Test the null session handler that stores no data."""
        self.new(self.common_session_test, session_manager=NullSessionStorage())
        self.reply("My name is Aiden", "Nice to meet you, undefined.")
        self.reply("Who am I?", "Aren't you undefined?")
        self.reply("What did I just say?", "You just said: undefined")
        self.reply("What did you just say?", "I just said: undefined")
        self.reply("I hate you", "How mean!")
        self.reply("My name is Aiden", "Nice to meet you, undefined.")

    def test_memory_session(self):
        """Test the default in-memory session store."""
        self.new(self.common_session_test)
        self.reply("My name is Aiden", "Nice to meet you, Aiden.")
        self.reply("What did I just say?", "You just said: my name is aiden")
        self.reply("Who am I?", "Aren't you Aiden?")
        self.reply("What did you just say?", "I just said: Aren't you Aiden?")
        self.reply("I hate you!", "How mean!")
        self.reply("My name is Bob", "Nope, I'm mad at you.")

    def test_freeze_thaw(self):
        """Test freezing and thawing variables."""
        self.new("""
            + my name is *
            - <set name=<formal>>Nice to meet you, <get name>.

            + who am i
            - Aren't you <get name>?
        """)
        self.reply("My name is Aiden", "Nice to meet you, Aiden.")
        self.reply("Who am I?", "Aren't you Aiden?")

        self.rs.freeze_uservars(self.username)
        self.reply("My name is Bob", "Nice to meet you, Bob.")
        self.reply("Who am I?", "Aren't you Bob?")

        self.rs.thaw_uservars(self.username)
        self.reply("Who am I?", "Aren't you Aiden?")
        self.rs.freeze_uservars(self.username)

        self.reply("My name is Bob", "Nice to meet you, Bob.")
        self.reply("Who am I?", "Aren't you Bob?")
        self.rs.thaw_uservars(self.username, "discard")
        self.reply("Who am I?", "Aren't you Bob?")

    def test_lastmatch(self):
        """Test the bug __lastmatch__ return u"undefined" is solved"""
        self.new("""
                    ! version = 2.0
                    + helo
                    - hello
                """)
        self.uservar('__lastmatch__', None) # Before any user input and reply, no match.
        self.reply("helo", "hello") # For matched case
        self.uservar('__lastmatch__','helo')
        self.reply("helo you","[ERR: No reply matched]") # For not-matched case
        self.uservar('__lastmatch__', None)
        self.reply("helo again","[ERR: No reply matched]") # For not-matched case again
        self.uservar('__lastmatch__', None)
        self.reply("helo", "hello")  # For matched case again
        self.uservar('__lastmatch__', 'helo')
