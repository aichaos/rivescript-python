#!/usr/bin/env python

"""interactive.py: RiveScript's built-in interactive mode.

To run this, run: python rivescript
              or: python __init__.py
              or: python __main__.py
The preferred method is the former."""

__docformat__ = 'plaintext'

import sys
import getopt
import json

from __init__ import RiveScript

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
        print json.dumps(resp)
        if stateful:
            print "__END__"
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

    print json.dumps(resp)
    if stateful:
        print "__END__"

def interactive_mode():
    # Get command line options.
    options, remainder = [], []
    try:
        options, remainder = getopt.getopt(sys.argv[1:], 'dju', ['debug',
                                                                'json',
                                                                'utf8',
                                                                'log=',
                                                                'strict',
                                                                'nostrict',
                                                                'depth=',
                                                                'help'])
    except:
        print "Unrecognized options given, try " + sys.argv[0] + " --help"
        exit()

    # Handle the options.
    debug, depth, strict = False, 50, True
    with_json, help, log = False, False, None
    utf8 = False
    for opt in options:
        if opt[0] == '--debug' or opt[0] == '-d':
            debug = True
        elif opt[0] == '--strict':
            strict = True
        elif opt[0] == '--nostrict':
            strict = False
        elif opt[0] == '--json':
            with_json = True
        elif opt[0] == '--utf8' or opt[0] == '-u':
            utf8 = True
        elif opt[0] == '--help' or opt[0] == '-h':
            help = True
        elif opt[0] == '--depth':
            depth = int(opt[1])
        elif opt[0] == '--log':
            log   = opt[1]

    # Help?
    if help:
        print """Usage: rivescript [options] <directory>

Options:

    --debug, -d
        Enable debug mode.

    --log FILE
        Log debug output to a file (instead of the console). Use this instead
        of --debug.

    --json, -j
        Communicate using JSON. Useful for third party programs.

    --strict, --nostrict
        Enable or disable strict mode (enabled by default).

    --depth=50
        Set the recursion depth limit (default is 50).

    --help
        Display this help.

JSON Mode:

    In JSON mode, input and output is done using JSON data structures. The
    format for incoming JSON data is as follows:

    {
        'username': 'localuser',
        'message': 'Hello bot!',
        'vars': {
            'name': 'Aiden'
        }
    }

    The format that would be expected from this script is:

    {
        'status': 'ok',
        'reply': 'Hello, human!',
        'vars': {
            'name': 'Aiden'
        }
    }

    If the calling program sends an EOF signal at the end of their JSON data,
    this script will print its response and exit. To keep a session going,
    send the string '__END__' on a line by itself at the end of your message.
    The script will do the same after its response. The pipe can then be used
    again for further interactions."""
        quit()

    # Given a directory?
    if len(remainder) == 0:
        print "Usage: rivescript [options] <directory>"
        print "Try rivescript --help"
        quit()
    root = remainder[0]

    # Make the bot.
    bot = RiveScript(
        debug=debug,
        strict=strict,
        depth=depth,
        utf8=utf8,
        log=log
    )
    bot.load_directory(root)
    bot.sort_replies()

    # Interactive mode?
    if with_json:
        # Read from standard input.
        buffer = ""
        stateful = False
        while True:
            line = ""
            try:
                line = raw_input().decode('utf8')
            except EOFError:
                break

            # Look for the __END__ line.
            end = re.match(r'^__END__$', line)
            if end:
                # Process it.
                stateful = True # This is a stateful session
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

    print "RiveScript Interpreter (Python) -- Interactive Mode"
    print "---------------------------------------------------"
    print "rivescript version: " + str(bot.VERSION())
    print "        Reply Root: " + root
    print ""
    print "You are now chatting with the RiveScript bot. Type a message and press Return"
    print "to send it. When finished, type '/quit' to exit the program."
    print "Type '/help' for other options."
    print ""

    while True:
        msg = raw_input("You> ").decode('utf8')

        # Commands
        if msg == '/help':
            print "> Supported Commands:"
            print "> /help   - Displays this message."
            print "> /quit   - Exit the program."
        elif msg == '/quit':
            exit()
        else:
            reply = bot.reply("localuser", msg)
            print "Bot>", reply
