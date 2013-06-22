#!/usr/bin/env python

# Example for how to set a Perl object handler.

import rivescript
from json import dumps, loads
from subprocess import Popen, PIPE

class PerlObject:
    """A Perl object handler for RiveScript."""
    _objects = {} # The cache of objects loaded

    def load(self, name, code):
        """Prepare a Perl code object given by the RS interpreter."""

        source = "\n".join(code)
        self._objects[name] = source

    def call(self, rs, name, user, fields):
        if not name in self._objects:
            return "[ERR: Object Not Found]"

        # JSON data to send to Perl.
        outgoing = dict(
            id=user,
            message=" ".join(fields),
            code=self._objects[name],
            vars={},
        )

        # Copy their current user vars over.
        vars = rs.get_uservars(user)
        for key, value in vars.iteritems():
            if type(value) != str:
                continue
            outgoing['vars'][key] = value

        # Fire up Perl and give it all this data.
        proc = Popen(["perl", "accomplice.pl"], stdin=PIPE, stdout=PIPE)
        proc.stdin.write(dumps(outgoing))
        proc.stdin.close()
        result = proc.stdout.read()

        # Hopefully that was JSON data we got!
        try:
            result = loads(result)
        except:
            return "[ERR: Got an unexpected result from Perl!]"

        # OK?
        if result['status'] == 'error':
            return "[ERR: %s]" % result['message']

        # Restore user variables from Perl, in case it changed anything.
        for key, value in result['vars'].iteritems():
            if type(value) != str:
                continue
            rs.set_uservar(user, key, value)

        return result['reply']

bot = rivescript.RiveScript()
bot.set_handler("perl", PerlObject())
bot.load_file("perl.rs")
bot.sort_replies()
while True:
    msg = raw_input("You> ")
    reply = bot.reply("localuser", msg)
    print "Bot>", reply

# vim:expandtab
