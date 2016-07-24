# RiveScript-Python
#
# This code is released under the MIT License.
# See the "LICENSE" file for more information.
#
# https://www.rivescript.com/

from __future__ import print_function, unicode_literals

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
    """The built-in RiveScript Interactive Mode.

    This feature of RiveScript allows you to test and debug a chatbot in your
    terminal window. There are two ways to invoke this mode::

        # By running the Python RiveScript module directly:
        python rivescript eg/brain

        # By running the shell.py in the source distribution:
        python shell.py eg/brain

    The only required command line parameter is a filesystem path to a directory
    containing RiveScript source files (with the ``*.rive`` file extension).

    Additionally, it accepts command line flags.

    Parameters:
        --utf8: Enable UTF-8 mode.
        --json: Use JSON to communicate with the bot instead of plain text.
            See the JSON Mode documentation below for advanced details.
        --debug: Enable verbose debug logging.
        --log (str): The path to a text file you want the debug logging to
            be written to. This is to be used in conjunction with ``--debug``,
            for the case where you don't want your terminal window to be flooded
            with debug messages.
        --depth (int): Override the recursion depth limit (default ``50``).
        --nostrict: Disable strict syntax checking when parsing the RiveScript
            files. By default a syntax error raises an exception and will
            terminate the interactive mode.
        --help: Show the documentation of command line flags.
        path (str): The path to a directory containing ``.rive`` files.

    **JSON Mode**

    By invoking the interactive mode with the ``--json`` (or ``-j``) flag,
    the interactive mode will communicate with you via JSON messages. This
    can be used as a "bridge" to enable the use of RiveScript from another
    programming language that doesn't have its own native RiveScript
    implementation.

    For example, a program could open a shell pipe to the RiveScript interactive
    mode and send/receive JSON payloads to communicate with the bot.

    In JSON mode, you send a message to the bot in the following format::

        {
            "username": "str username",
            "message": "str message",
            "vars": {
                "topic": "random",
                "name": "Alice"
            }
        }

    The ``username`` and ``message`` keys are required, and ``vars`` is a
    key/value object of all the variables about the user.

    After sending the JSON payload over standard input, you can either close the
    input file handle (send the EOF signal; or Ctrl-D in a terminal), or send
    the string ``__END__`` on a line of text by itself. This will cause the bot
    to parse your payload, get a reply for the message, and respond with a
    similar JSON payload::

        {
            "status": "ok",
            "reply": "str response",
            "vars": {
                "topic": "random",
                "name": "Alice"
            }
        }

    The ``vars`` structure in the response contains all of the key/value pairs
    the bot knows about the username you passed in. This will also contain a
    lot of internal data, such as the user's history and last matched trigger.

    To keep a stateful session, you should parse the ``vars`` returned by
    RiveScript and pass them in with your next request so that the bot can
    remember them for the next reply.

    If you closed the filehandle (Ctrl-D, EOF) after your input payload, the
    interactive mode will exit after giving the response. If, on the other
    hand, you sent the string ``__END__`` on a line by itself after your
    payload, the RiveScript interactive mode will do the same after its response
    is returned. This way, you can re-use the shell pipe to send and receive
    many messages over a single session.
    """

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
