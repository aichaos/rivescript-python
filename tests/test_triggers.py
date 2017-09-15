#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import unicode_literals, absolute_import

from rivescript.exceptions import RS_ERR_MATCH
from .config import RiveScriptTestCase

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

    def test_trigger_arrays_with_underscore(self):
        self.new("""
            ! array colors_bright = white blue

            + what color is my (@colors_bright) *
            - Your <star2> is <star1>.
        """)
        self.reply("What color is my white shirt?", "Your shirt is white.")

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

            + i like (@stars)
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
