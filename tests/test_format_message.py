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