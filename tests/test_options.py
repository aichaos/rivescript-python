#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import unicode_literals, absolute_import

from .config import RiveScriptTestCase

class ParserOptionTest(RiveScriptTestCase):
    """File scoped parser option tests."""

    def test_concat(self):
        self.new("""
            // Default concat mode = none
            + test concat default
            - Hello
            ^ world!

            ! local concat = space
            + test concat space
            - Hello
            ^ world!

            ! local concat = none
            + test concat none
            - Hello
            ^ world!

            ! local concat = newline
            + test concat newline
            - Hello
            ^ world!

            // invalid concat setting is equivalent to `none`
            ! local concat = foobar
            + test concat foobar
            - Hello
            ^ world!

            ! local concat = none
            + test concat
            ^ in trigger
            - Hello
            ^ world!

            ! local concat = none
            + [test] concat
            ^ \sin trigger with space and optional
            - Hello
            ^ \sworld!

            ! local concat = space
            + test concat space
            ^ in trigger
            - Hello
            ^ world!

            // the option is file scoped so it can be left at
            // any setting and won't affect subsequent parses
            ! local concat = newline
        """)
        self.extend("""
            // concat mode should be restored to the default in a
            // separate file/stream parse
            + test concat second file
            - Hello
            ^ world!
        """)

        self.reply("test concat default", "Helloworld!")
        self.reply("test concat space", "Hello world!")
        self.reply("test concat none", "Helloworld!")
        self.reply("test concat newline", "Hello\nworld!")
        self.reply("test concat second file", "Helloworld!")
        self.reply("test concatin trigger", "Helloworld!")
        self.reply("test concat in trigger with space and optional", "Hello world!")
        self.reply("test concat space in trigger", "Hello world!")
