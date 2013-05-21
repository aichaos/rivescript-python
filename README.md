RiveScript-Python
=================

INTRODUCTION
------------

This is a RiveScript interpreter for the Python programming language. RiveScript
is a scripting language for chatterbots, making it easy to write
trigger/response pairs for building up a bot's intelligence.

USAGE
-----

The `rivescript` module can be executed as a stand-alone Python script, or
included in other Python code. When executed directly, it launches an
interactive chat session:

	python rivescript ./brain

When used as a library, the synopsis is as follows:

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
	Copyright (C) 2012 Noah Petherbridge

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
