# RiveScript-Python

[![Build Status][1]][2] [![Read the docs][3]][4] [![PyPI][5]][6]

## Introduction

This is a RiveScript interpreter for the Python programming language. RiveScript
is a scripting language for chatterbots, making it easy to write
trigger/response pairs for building up a bot's intelligence.

This library is compatible with both Python 2 and Python 3.

## Documentation

Module documentation is available at <http://rivescript.readthedocs.org/>

Also check out the [**RiveScript Community Wiki**](https://github.com/aichaos/rivescript/wiki)
for common design patterns and tips & tricks for RiveScript.

## Installation

This module is available on [PyPI](https://pypi.python.org/) and can be
installed via pip:

`pip install rivescript`

To install manually, download or clone the git repository and run
`python setup.py install`

## Examples

There are examples available in the
[eg/](https://github.com/aichaos/rivescript-python/tree/master/eg) directory of
this project on GitHub that show how to interface with a RiveScript bot in a
variety of ways--such as through the Twilio SMS API--and other code snippets and
useful tricks.

## Usage

The `rivescript` module can be executed as a stand-alone Python script, or
included in other Python code. When executed directly, it launches an
interactive chat session:

    python rivescript ./eg/brain

In case running RiveScript as a script is inconvenient (for example, when it's
installed as a system module) you can use the `shell.py` script as an alias:

    python shell.py eg/brain

When used as a library, the synopsis is as follows:

```python
from rivescript import RiveScript

bot = RiveScript()
bot.load_directory("./eg/brain")
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

## UTF-8 Support

RiveScript supports Unicode but it is not enabled by default. Enable it by
passing a `True` value for the `utf8` option in the constructor, or by using the
`--utf8` argument to the standalone interactive mode.

In UTF-8 mode, most characters in a user's message are left intact, except for
certain metacharacters like backslashes and common punctuation characters like
`/[.,!?;:]/`.

If you want to override the punctuation regexp, you can provide a new one by
assigning the `unicode_punctuation` attribute of the bot object after
initialization. Example:

```python
import re
bot = RiveScript(utf8=True)
bot.unicode_punctuation = re.compile(r'[.,!?;:]')
```

Regardless of whether UTF-8 mode is on, all input messages given to the bot
are converted (if needed) to Python's `unicode` data type. So, while it's
good practice to make sure you're providing Unicode strings to the bot, the
library will have you covered if you forget.

## JSON Mode

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

## Contributors

* [Noah Petherbridge](https://github.com/kirsle)
* [Arash Saidi](https://github.com/arashsa)
* [Danilo Bargen](https://github.com/dbrgn)
* [FujiMakoto](https://github.com/FujiMakoto)
* [Hung Tu Dinh](https://github.com/Dinh-Hung-Tu)
* [Julien Syx](https://github.com/Seraf)
* [Pablo](https://github.com/flogiston)
* [Peixuan (Shawn) Ding](https://github.com/dinever)

## License

```
The MIT License (MIT)

Copyright (c) 2017 Noah Petherbridge

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

[1]: https://travis-ci.org/aichaos/rivescript-python.svg?branch=master
[2]: https://travis-ci.org/aichaos/rivescript-python
[3]: https://img.shields.io/badge/docs-latest-brightgreen.svg?style=flat
[4]: http://rivescript.rtfd.io/
[5]: https://img.shields.io/pypi/v/rivescript.svg
[6]: https://pypi.python.org/pypi/rivescript/
