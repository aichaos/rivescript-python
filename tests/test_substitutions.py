#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import unicode_literals, absolute_import

from .config import RiveScriptTestCase

class SubstitutionTests(RiveScriptTestCase):
    """Test substitutions."""

    def test_substitutions(self):
        self.new("""
            + whats up
            - nm.

            + what is up
            - Not much.
        """)
        self.reply("whats up", "nm.")
        self.reply("what's up?", "nm.")
        self.reply("what is up?", "Not much.")

        self.extend("""
            ! sub whats  = what is
            ! sub what's = what is
        """)
        self.reply("whats up", "Not much.")
        self.reply("what's up?", "Not much.")
        self.reply("What is up?", "Not much.")

    def test_person_substitutions(self):
        self.new("""
            + say *
            - <person>
        """)
        self.reply("say I am cool", "i am cool")
        self.reply("say You are dumb", "you are dumb")

        self.extend("""
            ! person i am    = you are
            ! person you are = I am
        """)
        self.reply("say I am cool", "you are cool")
        self.reply("say You are dumb", "I am dumb")
