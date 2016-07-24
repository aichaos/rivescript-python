#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import unicode_literals, absolute_import

from .config import RiveScriptTestCase

class BeginBlockTests(RiveScriptTestCase):
    """BEGIN Block Tests"""

    def test_no_begin_block(self):
        self.new("""
            + hello bot
            - Hello human.
        """)
        self.reply("Hello bot", "Hello human.")

    def test_simple_begin_block(self):
        self.new("""
            > begin
                + request
                - {ok}
            < begin

            + hello bot
            - Hello human.
        """)
        self.reply("Hello bot", "Hello human.")

    def test_blocked_begin_block(self):
        self.new("""
            > begin
                + request
                - Nope.
            < begin

            + hello bot
            - Hello human.
        """)
        self.reply("Hello bot", "Nope.")

    def test_conditional_begin_block(self):
        self.new("""
            > begin
                + request
                * <get met> == undefined => <set met=true>{ok}
                * <get name> != undefined => <get name>: {ok}
                - {ok}
            < begin

            + hello bot
            - Hello human.

            + my name is *
            - <set name=<formal>>Hello, <get name>.
        """)
        self.reply("Hello bot.", "Hello human.")
        self.uservar("met", "true")
        self.uservar("name", "undefined")
        self.reply("My name is bob", "Hello, Bob.")
        self.uservar("name", "Bob")
        self.reply("Hello Bot", "Bob: Hello human.")
