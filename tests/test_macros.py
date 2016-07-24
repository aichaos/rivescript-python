#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import unicode_literals, absolute_import

from .config import RiveScriptTestCase

class ObjectMacroTests(RiveScriptTestCase):
    """Test object macros."""

    def test_python_objects(self):
        self.new("""
            > object nolang
                return "Test w/o language."
            < object

            > object wlang python
                return "Test w/ language."
            < object

            > object reverse python
                msg = " ".join(args)
                return msg[::-1]
            < object

            > object broken python
                return "syntax error
            < object

            > object foreign javascript
                return "JavaScript checking in!"
            < object

            + test nolang
            - Nolang: <call>nolang</call>

            + test wlang
            - Wlang: <call>wlang</call>

            + reverse *
            - <call>reverse <star></call>

            + test broken
            - Broken: <call>broken</call>

            + test fake
            - Fake: <call>fake</call>

            + test js
            - JS: <call>foreign</call>
        """)
        self.reply("Test nolang", "Nolang: Test w/o language.")
        self.reply("Test wlang", "Wlang: Test w/ language.")
        self.reply("Reverse hello world", "dlrow olleh")
        self.reply("Test broken", "Broken: [ERR: Object Not Found]")
        self.reply("Test fake", "Fake: [ERR: Object Not Found]")
        self.reply("Test js", "JS: [ERR: Object Not Found]")

    def test_disabled_python_language(self):
        self.new("""
            > object test python
                return "Python here!"
            < object

            + test
            - Result: <call>test</call>
        """, debug=True)
        self.reply("test", "Result: Python here!")
        self.rs.set_handler("python", None)
        self.reply("test", "Result: [ERR: No Object Handler]")
