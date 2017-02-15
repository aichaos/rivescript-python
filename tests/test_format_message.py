#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import unicode_literals, absolute_import

from .config import RiveScriptTestCase

class MessageFormatTests(RiveScriptTestCase):
    """Test format message."""
    def test_format_message(self):
        self.new("""
            + hello bot
            - hello human
        """)
        self.reply("hello bot", "hello human")
        self.reply("Hello Bot", "hello human")
        self.reply("  hello bot   ", "hello human") # Strip leading and trailing whitespaces
        self.reply("  hello   bot   ", "hello human") # Replace the multiple whitespaces by single whitespace
        self.reply("hello      bot!!!???   ", "hello human") # Strip nasties

    def test_format_triggers(self):
        self.new("""
            + hi there
            -    hi   there

            +hi  here
            -hi  here

        """)
        self.reply("hi there", "hi there")
        self.reply("hi  here", "hi here")

    def test_invalid_character_raise_exception(self):
        self.assertRaises(Exception, self.new, """
                                + $hello
                                - hi
                            """)  # This test passes with `match`, which only check at the beginning
        self.assertRaises(Exception, self.new, """
                        + hello$
                        - hi
                    """)   # This test does not pass because the beginning is good, no $
        self.assertRaises(Exception, self.new, """
                            > topic Greetings
                                + hello
                                - hi
                            <topics
                            """)
        self.assertRaises(Exception, self.new, """
                                    > object hash %perl
                                      my ($rs, $args) = @_;
                                      my $method = shift @{$args};
                                    <object
                                    """)  # Test for character violation in object, no %