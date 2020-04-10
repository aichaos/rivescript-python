#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import unicode_literals, absolute_import

from .config import RiveScriptTestCase

import os
import shutil

class ImproveTestCoverage_Tests(RiveScriptTestCase):

    def test_improve_code_coverage_brain(self):
        self.new("""
            + *
            - star{topic=empty}

            > topic empty
            < topic
        """)
        self.reply("hi", "star")
        self.reply("hi", "[ERR: No Reply Matched]")         # Should give an "empty topic" warning
        # Doesn't work!  self.reply("hi", "star")                            # and put us back in "random"

        self.new("""
            + *
            @ recurse most deeply
        """)
        self.reply("recurse", "[ERR: Deep recursion detected]")

        self.new("""    // Trying to hit a bunch of code here! :-)
            + *
            - {random}star star{/random}<set var=var>{weight=2}

            + <input> <reply1> <get var>
            * 1 <= 2 => <get var> <reply> <input1> <add num=2><mult num=3><sub num=2><div num=2><get num>
            - Nope!

            + upper lower
            - {uppercase}lower{/uppercase} {lowercase}UPPER{/lowercase}

            + blank random
            - {random} {/random}blank

        """)
        self.reply("hi", "star")
        self.reply("hi star var", "var star hi 2")
        self.reply("upper lower", "LOWER upper")
        self.reply("blank random", "blank")

        from rivescript import RiveScript
        from rivescript.exceptions import RepliesNotSortedError
        self.rs = RiveScript()
        self.rs.stream("""
            + *
            - star
        """)
        try:
            self.reply("hi", "Nope!")
        except RepliesNotSortedError:
            pass

    def test_improve_code_coverage_parser(self):
        self.new("""
            + *         // Inline comment
            - star      // Another comment
        """)
        self.reply("hi", "star")

        self.new("""
            ! global g = gee
            ! global debug = false
            ! global depth = 100
            ! global strict = true
            ! var v = vee
            ! array a = a b c
            ! sub g = a
            ! person v = b

            // Now get rid of most of these

            ! global g = <undef>
            ! var v = <undef>
            ! array a = <undef>
            ! sub g = <undef>
            ! person v = <undef>

            + g
            - g <env g>

            + v *
            - <person> <bot v>

            + *
            - star

            + @a arr
            - a arr

        """)
        self.reply("g gee", "star")
        self.reply("g", "g undefined")
        self.reply("v v", "v undefined")
        self.reply("a arr", "star")
        # self.reply("arr", "a arr")

class RiveScript_Py_Tests(RiveScriptTestCase):
    def setUp(self):
        super().setUp()
        self.testdir = "__testdir__"
        os.mkdir(self.testdir)
        os.mkdir(os.path.join(self.testdir, "subdir"))
        def writeit(filename, contents):
            with open(os.path.join(self.testdir, filename), 'w') as f:
                f.write(contents + '\n')
        writeit("star.rive", """
            + *
            - star
        """)
        writeit("sub.rive", """
            ! sub aya = a
            ! sub bee = b
        """)
        writeit(os.path.join("subdir", "cont.rive"), """
            + a
            - aa

            + b
            - bb
        """)
        
    def tearDown(self):
        shutil.rmtree(self.testdir)

    def test_improve_code_coverage_rivescript(self):
        from rivescript import __version__
        from rivescript import RiveScript
        self.assertEqual(RiveScript.VERSION(), __version__)

        self.rs = RiveScript()
        self.rs.load_directory(self.testdir)
        self.rs.sort_replies()
        self.reply("a", "aa")
        self.reply("aya", "aa")
        self.reply("bee", "bb")
        self.reply("cee", "star")

        self.rs = RiveScript()
        self.rs.load_file(os.path.join(self.testdir, "star.rive"))
        self.rs.load_file(os.path.join(self.testdir, "subdir", "cont.rive"))
        self.rs.sort_replies()
        self.reply("a", "aa")
        self.reply("aya", "star")

        self.new("""
            ! global g = gee
            ! var    v = vee

            + g
            - <env g>

            + v
            - <bot v>
        """)
        self.reply("g", "gee")
        self.reply("v", "vee")
        self.rs.set_global("g", None)
        self.rs.set_variable("v", None)
        self.reply("g", "undefined")
        self.reply("v", "undefined")

        self.new("""
            + *
            - star<set m=me><set u=you>
        """)
        self.reply("hi", "star")
        self.assertContains(self.rs.get_uservars(), {self.username: {'m': "me", 'u': "you"}})
        self.rs.set_uservar("u2", "a", "aye")
        self.rs.clear_uservars(self.username)
        uv = self.rs.get_uservars()
        self.assertNotIn(self.username, uv)
        self.assertContains(uv, {"u2": {'a': "aye"}})

        self.new("""
            + u
            - <call>user</call>

            > object user python
                return rs.current_user()
            < object
        """)
        self.reply('u', self.username)
        self.assertEqual(self.rs.current_user(), None)

