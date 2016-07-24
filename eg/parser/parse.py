#!/usr/bin/env python

from __future__ import print_function
import codecs
import os
import json
import sys
from rivescript.parser import Parser

"""Example use of the RiveScript Parser module.

Usage: python parse.py [path/to/file.rive]

By default it will parse ../brain/clients.rive but you can pass it any
RiveScript file you want.
"""

def main():
    # Get the command line argument.
    filename = "../brain/clients.rive"
    if len(sys.argv) > 1:
        filename = sys.argv[1]

    # Make sure it's really a file.
    if not os.path.isfile(filename):
        print("{}: Not a file.".format(filename))
        sys.exit(1)

    # Make sure it looks like a RiveScript file.
    if not filename.lower().endswith(".rive"):
        print("{}: Doesn't look like a RiveScript file (no .rive extension)")
        sys.exit(1)

    # Create a parser instance.
    if os.environ.get("PARSER_DEBUG"):
        parser = Parser(
            on_debug=on_debug,
            on_warn=on_warn,
        )
    else:
        parser = Parser()

    # Read the file's contents.
    with codecs.open(filename, "r", "utf-8") as fh:
        source = fh.readlines()

        # Create a parser and parse it.
        ast = parser.parse(filename, source)

        # Dump the "Abstract Syntax Tree" to the console as JSON.
        print(json.dumps(ast, indent=2, sort_keys=True))

def on_debug(message):
    print("[DEBUG]", message)

def on_warn(message, filename=None, lineno=None):
    if filename is not None and lineno is not None:
        print("[WARN]", message, "at", filename, "line", lineno)
    else:
        print("[WARN]", message)

if __name__ == "__main__":
    main()
