RiveScript-Python
=================

INTRODUCTION
------------

This is a RiveScript interpreter for the Python programming language. RiveScript
is a scripting language for chatterbots, making it easy to write
trigger/response pairs for building up a bot's intelligence.

This library is compatible with both Python 2 and Python 3.

COMPILED RIVESCRIPT
-------------------

This branch includes some **experimental** code to support compiling RiveScript
documents into binary files using Google's Protocol Buffers.

When this module loads a RiveScript source file (`.rive`) it will feed it into a
Protocol Buffer message and then write the binary compiled version to disk as
a `.rivec` file (if it has permission to). On future attempts to load the same
RiveScript document again, it will use the pre-compiled version which can be
loaded into memory much more quickly.

If you make a change to the source `.rive` file, RiveScript will re-compile it
automatically. In this regard it works the same way Python does with their
`.py` vs. `.pyc` files.

USAGE
-----

The `rivescript` module can be executed as a stand-alone Python script, or
included in other Python code. When executed directly, it launches an
interactive chat session:

    python -m rivescript ./brain

When used as a library, the synopsis is as follows:

```python
from rivescript import RiveScript

bot = RiveScript()
bot.load_directory("./brain")
bot.sort_replies()

while True:
    msg = raw_input('You> ')
    if msg == '/quit':
        quit()

    reply = bot.reply("localuser", msg)
    print 'Bot>', reply
```

The scripts `example.py` and `example3.py` provide simple examples for using
RiveScript as a library for Python 2 and 3, respectively.

UTF-8 SUPPORT
-------------

Version 1.05 adds experimental support for UTF-8 in RiveScript. It is not
enabled by default. Enable it by passing a `True` value for the `utf8`
option in the constructor, or by using the `--utf8` (or `-u` for short)
option to the interactive mode.

By default (without UTF-8 mode on), triggers may only contain basic ASCII
characters (no foreign characters), and the user's message is stripped of
all characters except letters/numbers and spaces. This means that, for
example, you can't capture a user's e-mail address in a RiveScript reply,
because of the @ and . characters.

When UTF-8 mode is enabled, these restrictions are lifted. Triggers are only
limited to not contain certain metacharacters like the backslash, and the
user's message is only stripped of backslashes and HTML angled brackets (to
protect from obvious XSS if you use RiveScript in a web application). The
`<star>` tags in RiveScript will capture the user's "raw" input, so you can
write replies to get the user's e-mail address or store foreign characters
in their name.

Regardless of whether UTF-8 mode is on, all input messages given to the bot
are converted (if needed) to Python's `unicode` data type. So, while it's
good practice to make sure you're providing Unicode strings to the bot, the
library will have you covered if you forget.

JSON MODE
---------

The `rivescript` package, when run stand-alone, supports "JSON Mode", where
you communicate with the bot using JSON. This is useful for third-party
programs that want to use RiveScript but don't have an interpreter in their
native language.

Just run it like: `python rivescript --json /path/to/brain`

Print a JSON encoded data structure into the standard input. The format should
look like this:

	{
		"username": "localuser",
		"message": "Hello bot!",
		"vars": {
			"name": "Aiden"
		}
	}

After sending this, you can send an `EOF` signal and the bot will respond with
a JSON response and then exit. Or, you can keep the session open, by sending
the string `__END__` on a line by itself after your input. The bot will do the
same when it responds, so you can reuse the same pipe for multiple
interactions.

The bot's response will be formatted like so:

	{
		"status": "ok",
		"reply": "Hello, human!",
		"vars": {
			"name": "Aiden"
		}
	}

The `status` will be `ok` on success, or `error` if there was an error. The
`reply` is the bot's response (or an error message on error).

COPYRIGHT AND LICENSE
---------------------

The Python RiveScript interpreter is dual licensed. For open source applications
the module is licensed using the GNU General Public License, version 2. If you'd
like to use the Python RiveScript module in a closed source or commercial
application, contact the author for more information.

	RiveScript-Python
	Copyright (C) 2013 Noah Petherbridge

	This program is free software; you can redistribute it and/or modify
	it under the terms of the GNU General Public License as published by
	the Free Software Foundation; either version 2 of the License, or
	(at your option) any later version.

	This program is distributed in the hope that it will be useful,
	but WITHOUT ANY WARRANTY; without even the implied warranty of
	MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
	GNU General Public License for more details.

	You should have received a copy of the GNU General Public License
	along with this program; if not, write to the Free Software
	Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

SEE ALSO
--------

The official RiveScript website, http://www.rivescript.com/
