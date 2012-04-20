RiveScript-Python
=================

INTRODUCTION
------------

This is a RiveScript interpreter for the Python programming language. RiveScript
is a scripting language for chatterbots, making it easy to write
trigger/response pairs for building up a bot's intelligence.

USAGE
-----

The `rivescript.py` module can be executed as a stand-alone Python script, or
included in other Python code. When executed directly, it launches an
interactive chat session.

When used as a library, the synopsis is as follows:

	import rivescript

	bot = RiveScript()
	bot.load_directory("./brain")
	bot.sort_replies()
	
	reply = bot.reply("localuser", "Hello, bot!")
