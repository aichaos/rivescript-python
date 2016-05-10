#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import unicode_literals, absolute_import

import re
import unittest

from rivescript.rivescript import RS_ERR_MATCH

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


class BotvarTests(RiveScriptTestCase):
    """Test bot variables."""

    def test_bot_variables(self):
        self.new("""
            ! var name = Aiden
            ! var age = 5

            + what is your name
            - My name is <bot name>.

            + how old are you
            - I am <bot age>.

            + what are you
            - I'm <bot gender>.

            + happy birthday
            - <bot age=6>Thanks!
        """)
        self.reply("What is your name?", "My name is Aiden.")
        self.reply("How old are you?", "I am 5.")
        self.reply("What are you?", "I'm undefined.")
        self.reply("Happy birthday!", "Thanks!")
        self.reply("How old are you?", "I am 6.")


    def test_global_variables(self):
        self.new("""
            ! global debug = false

            + debug mode
            - Debug mode is: <env debug>

            + set debug mode *
            - <env debug=<star>>Switched to <star>.
        """)
        self.reply("Debug mode.", "Debug mode is: false")
        self.reply("Set debug mode true", "Switched to true.")
        self.reply("Debug mode?", "Debug mode is: true")


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


class TriggerTests(RiveScriptTestCase):
    """Test triggers."""

    def test_atomic_triggers(self):
        self.new("""
            + hello bot
            - Hello human.

            + what are you
            - I am a RiveScript bot.
        """)
        self.reply("Hello bot", "Hello human.")
        self.reply("What are you?", "I am a RiveScript bot.")


    def test_wildcard_triggers(self):
        self.new("""
            + my name is *
            - Nice to meet you, <star>.

            + * told me to say *
            - Why did <star1> tell you to say <star2>?

            + i am # years old
            - A lot of people are <star>.

            + i am _ years old
            - Say that with numbers.

            + i am * years old
            - Say that with fewer words.
        """)
        self.reply("my name is Bob", "Nice to meet you, bob.")
        self.reply("bob told me to say hi", "Why did bob tell you to say hi?")
        self.reply("i am 5 years old", "A lot of people are 5.")
        self.reply("i am five years old", "Say that with numbers.")
        self.reply("i am twenty five years old", "Say that with fewer words.")


    def test_alternatives_and_optionals(self):
        self.new("""
            + what (are|is) you
            - I am a robot.

            + what is your (home|office|cell) [phone] number
            - It is 555-1234.

            + [please|can you] ask me a question
            - Why is the sky blue?

            + (aa|bb|cc) [bogus]
            - Matched.

            + (yo|hi) [computer|bot] *
            - Matched.
        """)
        self.reply("What are you?", "I am a robot.")
        self.reply("What is you?", "I am a robot.")

        for kind in ["home", "office", "cell"]:
            self.reply("What is your {} phone number?".format(kind), "It is 555-1234.")
            self.reply("What is your {} number?".format(kind), "It is 555-1234.")

        self.reply("Can you ask me a question?", "Why is the sky blue?")
        self.reply("Please ask me a question?", "Why is the sky blue?")
        self.reply("Ask me a question?", "Why is the sky blue?")

        self.reply("aa", "Matched.")
        self.reply("bb", "Matched.")
        self.reply("aa bogus", "Matched.")
        self.reply("aabogus", RS_ERR_MATCH)
        self.reply("bogus", RS_ERR_MATCH)

        self.reply("hi Aiden", "Matched.")
        self.reply("hi bot how are you?", "Matched.")
        self.reply("yo computer what time is it?", "Matched.")
        self.reply("yoghurt is yummy", RS_ERR_MATCH)
        self.reply("hide and seek is fun", RS_ERR_MATCH)
        self.reply("hip hip hurrah", RS_ERR_MATCH)


    def test_trigger_arrays(self):
        self.new("""
            ! array colors = red blue green yellow white
              ^ dark blue|light blue

            + what color is my (@colors) *
            - Your <star2> is <star1>.

            + what color was * (@colors) *
            - It was <star2>.

            + i have a @colors *
            - Tell me more about your <star>.

            + i like @fruits
            - What?
        """)
        self.reply("What color is my red shirt?", "Your shirt is red.")
        self.reply("What color is my blue car?", "Your car is blue.")
        self.reply("What color is my pink house?", RS_ERR_MATCH)
        self.reply("What color is my dark blue jacket?", "Your jacket is dark blue.")
        self.reply("What color was Napoleon's white horse?", "It was white.")
        self.reply("What color was my red shirt?", "It was red.")
        self.reply("I have a blue car.", "Tell me more about your car.")
        self.reply("I have a cyan car.", RS_ERR_MATCH)
        self.reply("I like apples.", RS_ERR_MATCH)

    def test_nested_arrays(self):
        self.new("""
            ! array primary = red green blue
            ! array secondary = magenta cyan yellow
            ! array monochrome = gray grey white
            ! array rgb = @primary @secondary black
            ! array colors = @rgb @monochrome orange brown pink

            ! array animals = @birds @parrots dog
            ! array birds = chicken pigeon @animals
            ! array parrots = bluebonnet|budgerigar|ceram lory

            ! array female_singers = rihanna|ellie goulding|natasha khan
            ! array stars = @male_singers @female_singers

            + my bike is (@monochrome) *
            - I like monochrome bikes. Especially <star>!

            + is (@colors|beige) a color
            - Yes, <star> is a color.

            + is (@rgb) an rgb color
            - Yes, <star> is an RGB color!

            + my pet (@parrots) is called (*)
            - I like parrots! {sentence}<star2>{/sentence}... what a nice name for a <star1>.

            + my pet (@animals) is called (*)
            - {sentence}<star2>{/sentence}: what a nice name for a <star1>.

            + my favorite star is (@stars)
            - I like <star>, too!

            + my (@animals) is (*)
            - Why do you say your <star1> is <star2>?

        """)
        self.reply('My bike is grey and very fast.', 'I like monochrome bikes. Especially grey!')
        self.reply('Is red a color?', 'Yes, red is a color.')
        self.reply('Is beige a color?', 'Yes, beige is a color.')
        self.reply('Is carrot a color?', RS_ERR_MATCH)
        self.reply('Is black an RGB color?', 'Yes, black is an RGB color!')
        self.reply('Is pink an RGB color?', RS_ERR_MATCH)
        self.reply('My pet bluebonnet is called Stacy.', 'I like parrots! Stacy... what a nice name for a bluebonnet.')
        self.reply('My pet pigeon is called Lucy', RS_ERR_MATCH)
        self.reply('I like Rihanna.', RS_ERR_MATCH)
        self.reply('My dog is dumb!', 'Why do you say your dog is dumb?')

    def test_weighted_triggers(self):
        self.new("""
            + * or something{weight=10}
            - Or something. <@>

            + can you run a google search for *
            - Sure!

            + hello *{weight=20}
            - Hi there!
        """)
        self.reply("Hello robot.", "Hi there!")
        self.reply("Hello or something", "Hi there!")
        self.reply("Can you run a Google search for Python", "Sure!")
        self.reply("Can you run a Google search for Python or something", "Or something. Sure!")


class ReplyTests(RiveScriptTestCase):
    """Response tests."""

    def test_previous(self):
        self.new("""
            ! sub who's  = who is
            ! sub it's   = it is
            ! sub didn't = did not

            + knock knock
            - Who's there?

            + *
            % who is there
            - <sentence> who?

            + *
            % * who
            - Haha! <sentence>!

            + *
            - I don't know.
        """)
        self.reply("knock knock", "Who's there?")
        self.reply("Canoe", "Canoe who?")
        self.reply("Canoe help me with my homework?", "Haha! Canoe help me with my homework!")
        self.reply("hello", "I don't know.")


    def test_continuations(self):
        self.new("""
            + tell me a poem
            - There once was a man named Tim,\\s
            ^ who never quite learned how to swim.\\s
            ^ He fell off a dock, and sank like a rock,\\s
            ^ and that was the end of him.
        """)
        self.reply("Tell me a poem.",
            "There once was a man named Tim, " \
            + "who never quite learned how to swim. " \
            + "He fell off a dock, and sank like a rock, " \
            + "and that was the end of him.")


    def test_redirects(self):
        self.new("""
            + hello
            - Hi there!

            + hey
            @ hello

            + hi there
            - {@hello}
        """)
        for greeting in ["hello", "hey", "hi there"]:
            self.reply(greeting, "Hi there!")


    def test_conditionals(self):
        self.new("""
            + i am # years old
            - <set age=<star>>OK.

            + what can i do
            * <get age> == undefined => I don't know.
            * <get age> >  25 => Anything you want.
            * <get age> == 25 => Rent a car for cheap.
            * <get age> >= 21 => Drink.
            * <get age> >= 18 => Vote.
            * <get age> <  18 => Not much of anything.

            + am i your master
            * <get master> == true => Yes.
            - No.
        """)
        age_q = "What can I do?"
        self.reply(age_q, "I don't know.")

        ages = {
            '16' : "Not much of anything.",
            '18' : "Vote.",
            '20' : "Vote.",
            '22' : "Drink.",
            '24' : "Drink.",
            '25' : "Rent a car for cheap.",
            '27' : "Anything you want.",
        }
        for age in sorted(ages.keys()):
            self.reply("I am {} years old.".format(age), "OK.")
            self.reply(age_q, ages[age])

        self.reply("Am I your master?", "No.")
        self.rs.set_uservar(self.username, "master", "true")
        self.reply("Am I your master?", "Yes.")


    def test_embedded_tags(self):
        self.new("""
            + my name is *
            * <get name> != undefined => <set oldname=<get name>>I thought\s
              ^ your name was <get oldname>?
              ^ <set name=<formal>>
            - <set name=<formal>>OK.

            + what is my name
            - Your name is <get name>, right?

            + html test
            - <set name=<b>Name</b>>This has some non-RS <em>tags</em> in it.
        """)
        self.reply("What is my name?", "Your name is undefined, right?")
        self.reply("My name is Alice", "OK.")
        self.reply("My name is Bob.", "I thought your name was Alice?")
        self.reply("What is my name?", "Your name is Bob, right?")
        self.reply("HTML Test", "This has some non-RS <em>tags</em> in it.")


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


if __name__ == "__main__":
    unittest.main()
