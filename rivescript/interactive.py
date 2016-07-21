# RiveScript-Python
#
# This code is released under the MIT License.
# See the "LICENSE" file for more information.
#
# https://www.rivescript.com/

from __future__ import print_function, unicode_literals

"""interactive.py: RiveScript's built-in interactive mode.

To run this, run: python rivescript
              or: python __init__.py
              or: python __main__.py
The preferred method is the former."""

import argparse
import json
import re
from six.moves import input
from six import text_type

from rivescript import RiveScript

def json_in(bot, buffer, stateful):
    # Prepare the response.
    resp = {
        'status': 'ok',
        'reply': '',
        'vars': {}
    }

    # Decode the incoming JSON.
    try:
        incoming = json.loads(buffer)
    except:
        resp['status'] = 'error'
        resp['reply'] = 'Failed to decode incoming JSON data.'
        print(json.dumps(resp))
        if stateful:
            print("__END__")
        return

    # Username?
    username = "json"
    if 'username' in incoming:
        username = incoming["username"]

    # Decode their variables.
    if "vars" in incoming:
        for var in incoming["vars"]:
            bot.set_uservar(username, var, incoming["vars"][var])

    # Get a response.
    if 'message' in incoming:
        resp['reply'] = bot.reply(username, incoming["message"])
    else:
        resp['reply'] = "[ERR: No message provided]"

    # Retrieve vars.
    resp['vars'] = bot.get_uservars(username)

    print(json.dumps(resp))
    if stateful:
        print("__END__")


def interactive_mode():
    parser = argparse.ArgumentParser(description="RiveScript interactive mode.")
    parser.add_argument("--debug", "-d",
        help="Enable debug logging within RiveScript.",
        action="store_true",
    )
    parser.add_argument("--json", "-j",
        help="Enable JSON mode. In this mode, you communicate with the bot by "
            "sending a JSON-encoded object with keys 'username', 'message' and "
            "'vars' (an object of user variables) over standard input, and "
            "then close the input (^D) or send the string '__END__' on a line "
            "by itself. The bot will respond with a similarly formatted JSON "
            "response over standard output, and then will either exit or send "
            "'__END__' depending on how you ended your input.",
        action="store_true",
    )
    parser.add_argument("--utf8", "-u",
        help="Enable UTF-8 mode (default is disabled)",
        action="store_true",
    )
    parser.add_argument("--log",
        help="The path to a log file to send debugging output to (when debug "
            "mode is enabled) instead of standard output.",
        type=text_type,
    )
    parser.add_argument("--nostrict",
        help="Disable strict mode (where syntax errors are fatal)",
        action="store_true",
    )
    parser.add_argument("--depth",
        help="Override the default recursion depth limit when fetching a reply "
            "(default 50)",
        type=int,
        default=50,
    )
    parser.add_argument("path",
        help="A directory containing RiveScript files (*.rive) to load.",
        type=text_type,
        # required=True,
    )
    args = parser.parse_args()

    # Make the bot.
    bot = RiveScript(
        debug=args.debug,
        strict=not args.nostrict,
        depth=args.depth,
        utf8=args.utf8,
        log=args.log
    )
    bot.load_directory(args.path)
    bot.sort_replies()

    # Interactive mode?
    if args.json:
        # Read from standard input.
        buffer = ""
        stateful = False
        while True:
            line = ""
            try:
                line = input()
            except EOFError:
                break

            # Look for the __END__ line.
            end = re.match(r'^__END__$', line)
            if end:
                # Process it.
                stateful = True  # This is a stateful session
                json_in(bot, buffer, stateful)
                buffer = ""
                continue
            else:
                buffer += line + "\n"

        # We got the EOF. If the session was stateful, just exit,
        # otherwise process what we just read.
        if stateful:
            quit()
        json_in(bot, buffer, stateful)
        quit()

    print(
        "      .   .       \n"
        "     .:...::      RiveScript Interpreter (Python)\n"
        "    .::   ::.     Library Version: v{version}\n"
        " ..:;;. ' .;;:..  \n"
        "    .  '''  .     Type '/quit' to quit.\n"
        "     :;,:,;:      Type '/help' for more options.\n"
        "     :     :      \n"
        "\n"
        "Using the RiveScript bot found in: {path}\n"
        "Type a message to the bot and press Return to send it.\n"
        .format(version=bot.VERSION(), path=args.path)
    )

    while True:
        msg = input("You> ")

        # Commands
        if msg == '/help':
            print("> Supported Commands:")
            print("> /help   - Displays this message.")
            print("> /quit   - Exit the program.")
        elif msg == '/quit':
            exit()
        else:
            reply = bot.reply("localuser", msg)
            print("Bot>", reply)
