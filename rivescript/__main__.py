#!/usr/bin/env python

from __future__ import absolute_import

"""RiveScript's __main__.py

This script is executed when you run `python rivescript` directly.
It does nothing more than load the interactive mode of RiveScript."""

__docformat__ = 'plaintext'

# Boilerplate to allow running as script directly.
# See: http://stackoverflow.com/questions/2943847/nightmare-with-relative-imports-how-does-pep-366-work
if __name__ == "__main__" and not __package__:
    import sys, os
    parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.insert(0, parent_dir)
    import rivescript
    __package__ = str("rivescript")

    from .interactive import interactive_mode
    interactive_mode()

# vim:expandtab
