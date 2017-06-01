# RiveScript-Python
#
# This code is released under the MIT License.
# See the "LICENSE" file for more information.
#
# https://www.rivescript.com/

from __future__ import unicode_literals
import re

"""Common regular expressions used in RiveScript."""

# Common regular expressions.
class RE(object):
    equals      = re.compile('\s*=\s*')
    ws          = re.compile('\s+')
    objend      = re.compile('^\s*<\s*object')
    weight      = re.compile(r'\s*\{weight=(\d+)\}\s*')
    inherit     = re.compile('\{inherits=(\d+)\}')
    wilds_and_optionals = re.compile('[\s\*\#\_\[\]()]+')
    nasties     = re.compile('[^A-Za-z0-9 ]')
    crlf        = re.compile('<crlf>')
    literal_w   = re.compile(r'\\w')
    array       = re.compile(r'\@(.+?)\b')
    reply_array = re.compile(r'\(@([A-Za-z0-9_]+)\)')
    ph_array    = re.compile(r'\x00@([A-Za-z0-9_]+)\x00')
    def_syntax  = re.compile(r'^.+(?:\s+.+|)\s*=\s*.+?$')
    name_syntax = re.compile(r'[^a-z0-9_\-\s]')
    obj_syntax  = re.compile(r'[^A-Za-z0-9_\-\s]')
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
    empty_pipe   = re.compile(r'\|\s*\||\[\s*\||\|\s*\]|\(\s*\||\|\s*\)')  # ||, [|, |], (|, |)
