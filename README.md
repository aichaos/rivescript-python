# RiveScript-Python

## INTRODUCTION

This is a RiveScript interpreter for the Python programming language. RiveScript
is a scripting language for chatterbots, making it easy to write
trigger/response pairs for building up a bot's intelligence.

This library is compatible with both Python 2 and Python 3.

## USAGE

The `rivescript` module can be executed as a stand-alone Python script, or
included in other Python code. When executed directly, it launches an
interactive chat session:

    python rivescript ./brain

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

## UTF-8 SUPPORT

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

## JSON MODE

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

## LICENSE

```
The MIT License (MIT)

Copyright (c) 2015 Noah Petherbridge

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

SEE ALSO
--------

The official RiveScript website, http://www.rivescript.com/
