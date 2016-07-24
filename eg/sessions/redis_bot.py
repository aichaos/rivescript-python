#!/usr/bin/env python

from __future__ import unicode_literals, print_function, absolute_import
from six.moves import input
import sys
from rivescript import RiveScript
from redis_storage import RedisSessionStorage

bot = RiveScript(
    session_manager=RedisSessionStorage(),
)
bot.load_directory("../brain")
bot.sort_replies()

print("""RiveScript Redis Session Storage Example

This example uses a Redis server to store user variables. For the sake of the
example, choose a username to store your variables under. You can re-run this
script with the same username (or a different one!) and verify that your
variables are kept around!

Type '/quit' to quit.
""")

username = input("What is your username? ").strip()
if len(username) == 0:
    print("You need to enter one! This script will exit now.")
    sys.exit(1)

while True:
    message = input("You> ").strip()
    if len(message) == 0:
        continue

    if message.startswith("/quit"):
        sys.exit(1)

    reply = bot.reply(username, message)
    print("Bot>", reply)
