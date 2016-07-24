#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import unicode_literals, absolute_import

from rivescript.exceptions import RS_ERR_MATCH
from .config import RiveScriptTestCase

class TopicTest(RiveScriptTestCase):
    """Topic tests."""

    def test_punishment_topic(self):
        self.new("""
            + hello
            - Hi there!

            + swear word
            - How rude! Apologize or I won't talk to you again.{topic=sorry}

            + *
            - Catch-all.

            > topic sorry
                + sorry
                - It's ok!{topic=random}

                + *
                - Say you're sorry!
            < topic
        """)
        self.reply("hello", "Hi there!")
        self.reply("How are you?", "Catch-all.")
        self.reply("Swear word!", "How rude! Apologize or I won't talk to you again.")
        self.reply("hello", "Say you're sorry!")
        self.reply("How are you?", "Say you're sorry!")
        self.reply("Sorry!", "It's ok!")
        self.reply("hello", "Hi there!")
        self.reply("How are you?", "Catch-all.")

    def test_topic_inheritence(self):
        self.new("""
            > topic colors
                + what color is the sky
                - Blue.

                + what color is the sun
                - Yellow.
            < topic

            > topic linux
                + name a red hat distro
                - Fedora.

                + name a debian distro
                - Ubuntu.
            < topic

            > topic stuff includes colors linux
                + say stuff
                - "Stuff."
            < topic

            > topic override inherits colors
                + what color is the sun
                - Purple.
            < topic

            > topic morecolors includes colors
                + what color is grass
                - Green.
            < topic

            > topic evenmore inherits morecolors
                + what color is grass
                - Blue, sometimes.
            < topic
        """)

        self.rs.set_uservar(self.username, "topic", "colors")
        self.reply("What color is the sky?", "Blue.")
        self.reply("What color is the sun?", "Yellow.")
        self.reply("What color is grass?", RS_ERR_MATCH)
        self.reply("Name a Red Hat distro.", RS_ERR_MATCH)
        self.reply("Name a Debian distro.", RS_ERR_MATCH)
        self.reply("Say stuff.", RS_ERR_MATCH)

        self.rs.set_uservar(self.username, "topic", "linux")
        self.reply("What color is the sky?", RS_ERR_MATCH)
        self.reply("What color is the sun?", RS_ERR_MATCH)
        self.reply("What color is grass?", RS_ERR_MATCH)
        self.reply("Name a Red Hat distro.", "Fedora.")
        self.reply("Name a Debian distro.", "Ubuntu.")
        self.reply("Say stuff.", RS_ERR_MATCH)

        self.rs.set_uservar(self.username, "topic", "stuff")
        self.reply("What color is the sky?", "Blue.")
        self.reply("What color is the sun?", "Yellow.")
        self.reply("What color is grass?", RS_ERR_MATCH)
        self.reply("Name a Red Hat distro.", "Fedora.")
        self.reply("Name a Debian distro.", "Ubuntu.")
        self.reply("Say stuff.", '"Stuff."')

        self.rs.set_uservar(self.username, "topic", "override")
        self.reply("What color is the sky?", "Blue.")
        self.reply("What color is the sun?", "Purple.")
        self.reply("What color is grass?", RS_ERR_MATCH)
        self.reply("Name a Red Hat distro.", RS_ERR_MATCH)
        self.reply("Name a Debian distro.", RS_ERR_MATCH)
        self.reply("Say stuff.", RS_ERR_MATCH)

        self.rs.set_uservar(self.username, "topic", "morecolors")
        self.reply("What color is the sky?", "Blue.")
        self.reply("What color is the sun?", "Yellow.")
        self.reply("What color is grass?", "Green.")
        self.reply("Name a Red Hat distro.", RS_ERR_MATCH)
        self.reply("Name a Debian distro.", RS_ERR_MATCH)
        self.reply("Say stuff.", RS_ERR_MATCH)

        self.rs.set_uservar(self.username, "topic", "evenmore")
        self.reply("What color is the sky?", "Blue.")
        self.reply("What color is the sun?", "Yellow.")
        self.reply("What color is grass?", "Blue, sometimes.")
        self.reply("Name a Red Hat distro.", RS_ERR_MATCH)
        self.reply("Name a Debian distro.", RS_ERR_MATCH)
        self.reply("Say stuff.", RS_ERR_MATCH)
