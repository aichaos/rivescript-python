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

    def test_check_syntax(self):
        mismatch_brackets = ["a (b", "a [b", "a {b", "a <b", "a b)", "a b]", "a b}", "a b>"]
        empty_pipes = ["[a|b| ]", "[a|b|]", "[a| |c]", "[a||c]", "[ |b|c]", "[|b|c]"]
        advanced_brackets = [") a (", "] b [", "> c <", "} d {", "a (b [c) d]", "a (b [c|d) e]"]
        angle_brackets = ["(a <b) c>", "<a (b > c)", "[a <b ] c>", "< a [b > c]", "{ a < b } c >", "< a {b > c }"]
        pipe_outside = ["a|b", "a|", "|b", "(a|b) | (c|d)", "(a|b)|(c|d)"]

        for failing_trigger in mismatch_brackets + empty_pipes + advanced_brackets + pipe_outside + angle_brackets:
            self.assertRaises(Exception, self.new, """
                + {}
                - hi
            """.format(failing_trigger))

        self.new("""
            ! version = 2.0

            // Bot variables
            ! var name = Tutorial
            ! var nickname = tut

            + [<bot name>|<nickname>] *
            - You called?
        """)
        self.reply("Tutorial", "You called?")
        self.reply("tut", "You called?")

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
        self.new("""
            > object hash Perl
                my ($rs, $args) = @_;
                my $method = shift @{$args};
            <object
        """) # No exception raised for uppercase character in object

    def test_space_tolerance_with_pipe(self):
        self.new("""
                    + hey [ a | b|c ]
                    - hi
                """)
        for message in ['hey a', 'hey b', 'hey c']:
            self.reply(message, "hi")
