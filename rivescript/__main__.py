#!/usr/bin/env python

"""RiveScript's __main__.py

This script is executed when you run `python rivescript` directly.
It does nothing more than load the interactive mode of RiveScript."""

__docformat__ = 'plaintext'

from interactive import interactive_mode

if __name__ == "__main__":
    interactive_mode()

# vim:expandtab
