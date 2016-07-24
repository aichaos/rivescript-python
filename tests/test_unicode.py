#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import unicode_literals, absolute_import

import re
from rivescript.exceptions import RS_ERR_MATCH
from .config import RiveScriptTestCase

class UnicodeTest(RiveScriptTestCase):
    """UTF-8 Tests."""

    def test_unicode(self):
        self.new("""
            ! sub who's = who is

            + äh
            - What's the matter?

            + ブラッキー
            - エーフィ

            // Make sure %Previous continues working in UTF-8 mode.
            + knock knock
            - Who's there?

            + *
            % who is there
            - <sentence> who?

            + *
            % * who
            - Haha! <sentence>!

            // And with UTF-8.
            + tëll më ä pöëm
            - Thërë öncë wäs ä män nämëd Tïm

            + more
            % thërë öncë wäs ä män nämëd tïm
            - Whö nëvër qüïtë lëärnëd höw tö swïm

            + more
            % whö nëvër qüïtë lëärnëd höw tö swïm
            - Hë fëll öff ä döck, änd sänk lïkë ä röck

            + more
            % hë fëll öff ä döck änd sänk lïkë ä röck
            - Änd thät wäs thë ënd öf hïm.
        """, utf8=True)

        self.reply("äh", "What's the matter?")
        self.reply("ブラッキー", "エーフィ")
        self.reply("knock knock", "Who's there?")
        self.reply("Orange", "Orange who?")
        self.reply("banana", "Haha! Banana!")
        self.reply("tëll më ä pöëm", "Thërë öncë wäs ä män nämëd Tïm")
        self.reply("more", "Whö nëvër qüïtë lëärnëd höw tö swïm")
        self.reply("more", "Hë fëll öff ä döck, änd sänk lïkë ä röck")
        self.reply("more", "Änd thät wäs thë ënd öf hïm.")

    def test_unicode_punctuation(self):
        self.new("""
            + hello bot
            - Hello human!
        """, utf8=True)

        self.reply("Hello bot", "Hello human!")
        self.reply("Hello, bot", "Hello human!")
        self.reply("Hello: bot", "Hello human!")
        self.reply("Hello... bot?", "Hello human!")

        # Edit the punctuation regexp.
        self.rs.unicode_punctuation = re.compile(r'xxx')
        self.reply("Hello bot", "Hello human!")
        self.reply("Hello, bot!", RS_ERR_MATCH)
