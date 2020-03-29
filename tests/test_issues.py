#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import unicode_literals, absolute_import

from .config import RiveScriptTestCase

import io

class IssueTests(RiveScriptTestCase):
    """Test reported issues."""

    def test_brain_transplant_issue_81(self):
        for i in range(0x100):      # One bit for each 'preserve_' option
            preserve_globals     = (i & 1)
            preserve_vars        = (i & 2) >> 1
            preserve_uservars    = (i & 4) >> 2
            preserve_handlers    = (i & 8) >> 3
            preserve_subroutines = (i & 0x10) >> 4
            preserve_substitutions = (i & 0x20) >> 5
            preserve_persons     = (i & 0x40) >> 6
            preserve_arrays      = (i & 0x80) >> 7
            with self.subTest(preserve_globals=preserve_globals,
                    preserve_vars=preserve_vars,
                    preserve_uservars=preserve_uservars,
                    preserve_handlers=preserve_handlers,
                    preserve_subroutines=preserve_subroutines,
                    preserve_substitutions=preserve_substitutions,
                    preserve_persons=preserve_persons,
                    preserve_arrays = preserve_arrays):
                self.new("""
                    ! array ar = a b
                    ! global gv = global_value
                    ! var vv = var_value
                    ! sub s = subbed
                    ! person i = you

                    + hello *
                    - <set uv=uv_value><call>sub</call><call>py</call><person>


                    > object py python
                        return "py"
                    < object
                """)
                def sub(rs, args):
                    return "hi"
                self.rs.set_subroutine("sub", sub)
                self.reply("hello i", "hipyyou")
                self.uservar("uv", "uv_value")
                self.assertEqual(self.rs.get_global("gv"), "global_value")
                self.assertEqual(self.rs.get_variable("vv"), "var_value")
                self.rs.set_handler('python', None)
                if i == 0x7F:       # This is the default
                    self.rs.prepare_brain_transplant()
                else:
                    self.rs.prepare_brain_transplant(preserve_globals=preserve_globals,
                      preserve_vars=preserve_vars, preserve_uservars=preserve_uservars,
                      preserve_handlers=preserve_handlers, preserve_subroutines=preserve_subroutines,
                      preserve_substitutions=preserve_substitutions, preserve_persons=preserve_persons,
                      preserve_arrays = preserve_arrays)
                self.assertEqual(self.rs.get_global("gv"), ("undefined", "global_value")[preserve_globals])
                self.assertEqual(self.rs.get_variable("vv"), ("undefined", "var_value")[preserve_vars])
                self.uservar("uv", (None, "uv_value")[preserve_uservars])
                self.extend("""
                    + arr (@ar)
                    - array

                    + hi
                    - <call>sub</call>

                    + call py
                    - <call>py</call>

                    + subbed
                    - ess

                    + *
                    - <person>

                    + new brain
                    - Passed!
                """)
                self.rs.sort_replies()
                self.reply("arr b", ("arr b", "array")[preserve_arrays])
                hi_reply = ("[ERR: Object Not Found]", "[ERR: No Object Handler]", "[ERR: Object Not Found]", "hi") \
                    [preserve_subroutines+((not preserve_handlers)<<1)]
                self.reply("hi", hi_reply)
                self.reply("s", ("s", "ess")[preserve_substitutions])
                self.reply("i", ("i", "you")[preserve_persons])
                self.reply("hello", "hello")
                py_reply = hi_reply
                if py_reply == "hi":
                    py_reply = "py"
                self.reply("call py", py_reply)
                self.reply("new brain", "Passed!")

    def test_trigger_info_issue_120(self):
        self.new("""
            + *
            - star

            + last *
            % star
            - match{topic=subtop}

            > topic subtop inherits random
                + sub top
                - subtop reply{topic=random}
            < topic
        """)
        self.reply("s", "star")
        self.assertEqual(self.rs.last_match(self.username), '*')
        response1 = dict(topic="random", trigger="*", previous=None, filename="stream()", lineno=2)
        self.assertEqual(self.rs.trigger_info(topic="random", trigger='*', user=self.username), [response1])
        self.reply("last match", "match")
        self.assertEqual(self.rs.last_match(self.username), 'last *')
        response2 = dict(topic="random", trigger="last *", previous="star", filename="stream()", lineno=5)
        self.assertEqual(self.rs.trigger_info(topic="random", trigger='last *', user=self.username, last_reply="star"), [response2])
        self.assertEqual(self.rs.trigger_info(trigger='last *', user=self.username, last_reply="star"), [response2])
        self.assertEqual(self.rs.trigger_info(trigger='last *', user=self.username), [response2])
        self.assertEqual(self.rs.trigger_info(trigger='last *'), [response2])
        self.assertEqual(self.rs.trigger_info(trigger='last *', user=self.username, last_reply="Nope!"), None)
        self.reply("sub top", "subtop reply")
        response3 = dict(topic="subtop", trigger="sub top", previous=None, filename="stream()", lineno=10)
        self.assertEqual(self.rs.trigger_info(topic="subtop", trigger='sub top'), [response3])
        self.assertEqual(self.rs.trigger_info(topic="subtop"), [response3])
        self.assertEqual(self.rs.trigger_info(trigger='sub top'), [response3])
        self.assertEqual(self.rs.trigger_info(), [response1, response2, response3])
        self.assertEqual(self.rs.trigger_info(topic="not found"), None)
        self.assertEqual(self.rs.trigger_info(topic="random", trigger="not found"), None)
        self.assertEqual(self.rs.trigger_info(trigger="not found"), None)

    def test_equal_in_var_issue_130(self):
        self.new("""
            ! global website = https://www.rivescript.com/try/#/doc?x=y&more=global
            ! var website    = https://www.rivescript.com/try/#/doc?x=y&more=var

            + global
            - <env website>

            + var
            - <bot website>

        """)
        self.reply("global", "https://www.rivescript.com/try/#/doc?x=y&more=global")
        self.reply("var", "https://www.rivescript.com/try/#/doc?x=y&more=var")

    def test_nested_brackets_issue_132(self):
        self.new("""
            + ((cat|dog) [*] animal|animal [*] (cat|dog))
            - Passed

            + *
            - Default
        """)
        self.reply("cat is an animal", "Passed")
        self.reply("dog is an animal", "Passed")
        self.reply("animal is a cat", "Passed")
        self.reply("animal is a dog", "Passed")
        self.reply("cat animal dog", "Default")
        self.reply("the animal is a dog", "Default")

    def test_sorting_multi_optionals_issue_133(self):
        self.new("""
            + [*] what [*] fram is [*]
            - Failed

            + [*] what [*] flow [*] getting [*] reviewed [*] fram is answer type [*]
            - Passed

            + hey
            @ what flow getting reviewed fram is answer type
        """)
        self.reply("hey", "Passed")

    def test_incomment_debug_msg_issue_138(self):
        logit = io.StringIO()

        self.new("""
            /* Start of comment
             * middle of comment
             */

            + *
            - Default
        """, debug=True, log=logit)
        self.reply("hi", "Default")
        self.assertTrue("incomment: True, " in logit.getvalue())

        logit = io.StringIO()

        self.new("""
            > object myobj python
              return "Default"
            < object

            + *
            - <call>myobj</call>
        """, debug=True, log=logit)
        self.reply("hi", "Default")
        self.assertFalse("incomment: True" in logit.getvalue())

    def test_not_subbing_4x_issue_140(self):
        self.new("""
            + a a a a
            - Got a a a a

            + a a ab a
            - Got a a ab a

            ! sub ab = a

        """)
        self.reply("ab ab ab ab", "Got a a a a")

    def test_set_substitution_issue_142(self):
        self.new("""
            + hello
            - hi

            + *
            - default
        """)
        self.rs.set_substitution("h", "hello")
        self.rs.sort_replies()
        self.reply("h", "hi")
        self.rs.set_substitution("h", None)
        self.rs.sort_replies()
        self.reply("h", "default")

    def test_set_person_issue_143(self):
        self.new("""
            + i *
            - <person>
        """)
        self.rs.set_person("i", "you")
        self.rs.sort_replies()
        self.reply("i i", "you")
        self.rs.set_person("i", None)
        self.rs.sort_replies()
        self.reply("i i", "i")

