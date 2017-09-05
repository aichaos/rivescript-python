#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import unicode_literals, absolute_import
from six.moves import cStringIO as StringIO

from .config import RiveScriptTestCase

class DeparseTests(RiveScriptTestCase):
    """Test deparse and write functions."""
    maxDiff = 8000

    def test_deparse(self):
        # The original source that should match the re-written version.
        source = """// Written by rivescript.deparse()
            ! version = 2.0

            ! var age = 5
            ! var name = Aiden

            > begin

                + request
                - {ok}

            < begin

            + what is your name
            - My name is <bot name>.

            + my name is *
            - <set name=<formal>>Nice to meet you.

            + you too
            % nice to meet you
            - :)

            + who am i
            * <get name> != undefined => Aren't you <get name>?
            - I don't know.
            - We've never met.

            > topic a includes b

                + a
                - A.

            < topic

            > topic b

                + b
                - B.

            < topic

            > topic c inherits b includes a

                + c
                - C.

            < topic
        """

        # Expected deparsed data structure.
        expected = {
            "begin": {
                "global": {},
                "var": {
                    "name": "Aiden",
                    "age": "5",
                },
                "sub": {},
                "person": {},
                "array": {},
                "triggers": [{
                    "trigger": "request",
                    "reply": ["{ok}"],
                    "condition": [],
                    "redirect": None,
                    "previous": None,
                }],
            },
            "topics": {
                "random": {
                    "includes": {},
                    "inherits": {},
                    "triggers": [
                        {
                            "trigger": "what is your name",
                            "previous": None,
                            "redirect": None,
                            "condition": [],
                            "reply": ["My name is <bot name>."]
                        },
                        {
                            "trigger": "my name is *",
                            "previous": None,
                            "redirect": None,
                            "condition": [],
                            "reply": ["<set name=<formal>>Nice to meet you."],
                        },
                        {
                            "trigger": "you too",
                            "previous": "nice to meet you",
                            "redirect": None,
                            "condition": [],
                            "reply": [":)"],
                        },
                        {
                            "trigger": "who am i",
                            "previous": None,
                            "redirect": None,
                            "condition": [
                                "<get name> != undefined => Aren't you <get name>?",
                            ],
                            "reply": ["I don't know.", "We've never met."],
                        },
                    ]
                },
                "a": {
                    "includes": { "b": 1 },
                    "inherits": {},
                    "triggers": [{
                        "trigger": "a",
                        "previous": None,
                        "redirect": None,
                        "condition": [],
                        "reply": ["A."],
                    }],
                },
                "b": {
                    "includes": {},
                    "inherits": {},
                    "triggers": [{
                        "trigger": "b",
                        "previous": None,
                        "redirect": None,
                        "condition": [],
                        "reply": ["B."],
                    }],
                },
                "c": {
                    "includes": {"a": 1},
                    "inherits": {"b": 1},
                    "triggers": [{
                        "trigger": "c",
                        "previous": None,
                        "redirect": None,
                        "condition": [],
                        "reply": ["C."],
                    }],
                }
            }
        }

        # Verify the deparsed tree matches expectations.
        self.new(source)
        dep = self.rs.deparse()
        self.assertEqual(dep, expected)

        # See if the re-written RiveScript source matches the original.
        buf = StringIO()
        self.rs.write(buf)
        written = buf.getvalue().split("\n")
        for i, line in enumerate(source.split("\n")):
            assert line.strip() == written[i].strip()
