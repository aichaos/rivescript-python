#!/usr/bin/env python

# The MIT License (MIT)
#
# Copyright (c) 2016 Noah Petherbridge
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

from __future__ import unicode_literals
import re

"""Common regular expressions used in RiveScript."""

# Common regular expressions.
class RE(object):
    equals      = re.compile('\s*=\s*')
    ws          = re.compile('\s+')
    objend      = re.compile('^\s*<\s*object')
    weight      = re.compile('\{weight=(\d+)\}')
    inherit     = re.compile('\{inherits=(\d+)\}')
    wilds       = re.compile('[\s\*\#\_]+')
    nasties     = re.compile('[^A-Za-z0-9 ]')
    crlf        = re.compile('<crlf>')
    literal_w   = re.compile(r'\\w')
    array       = re.compile(r'\@(.+?)\b')
    def_syntax  = re.compile(r'^.+(?:\s+.+|)\s*=\s*.+?$')
    name_syntax = re.compile(r'[^a-z0-9_\-\s]')
    utf8_trig   = re.compile(r'[A-Z\\.]')
    trig_syntax = re.compile(r'[^a-z0-9(\|)\[\]*_#@{}<>=\s]')
    cond_syntax = re.compile(r'^.+?\s*(?:==|eq|!=|ne|<>|<|<=|>|>=)\s*.+?=>.+?$')
    utf8_meta   = re.compile(r'[\\<>]')
    utf8_punct  = re.compile(r'[.?,!;:@#$%^&*()]')
    cond_split  = re.compile(r'\s*=>\s*')
    cond_parse  = re.compile(r'^(.+?)\s+(==|eq|!=|ne|<>|<|<=|>|>=)\s+(.+?)$')
    topic_tag   = re.compile(r'\{topic=(.+?)\}')
    set_tag     = re.compile(r'<set (.+?)=(.+?)>')
    bot_tag     = re.compile(r'<bot (.+?)>')
    get_tag     = re.compile(r'<get (.+?)>')
    star_tags   = re.compile(r'<star(\d+)>')
    botstars    = re.compile(r'<botstar(\d+)>')
    input_tags  = re.compile(r'<input([1-9])>')
    reply_tags  = re.compile(r'<reply([1-9])>')
    random_tags = re.compile(r'\{random\}(.+?)\{/random\}')
    redir_tag   = re.compile(r'\{@(.+?)\}')
    tag_search  = re.compile(r'<([^<]+?)>')
    placeholder = re.compile(r'\x00(\d+)\x00')
    zero_star   = re.compile(r'^\*$')
    optionals   = re.compile(r'\[(.+?)\]')
