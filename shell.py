#!/usr/bin/env python

"""shell.py: a shortcut to running RiveScript in interactive mode.

Running this script is equivalent to running `python rivescript` and it
accepts all the same parameters. This script is provided as a convenience
in case running the RiveScript module as a script is inconvenient (e.g.
when it's installed as a system module at some long path under
/usr/lib/python/...)"""

from rivescript.interactive import interactive_mode

if __name__ == "__main__":
    interactive_mode()
