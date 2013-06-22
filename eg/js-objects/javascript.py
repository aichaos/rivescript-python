# vim:expandtab

# Example for how to set a JavaScript object handler.

import rivescript

class JSObject:
    """A JavaScript handler for RiveScript."""
    _objects = {} # The cache of objects loaded

    def load(self, name, code):
        """Prepare a JavaScript code object given by the RS interpreter."""

        source = "function RSOBJ_" + name + "(args) {\n" + "\n".join(code) + "}\n"
        self._objects[name] = source

    def call(self, rs, name, user, fields):
        if not name in self._objects:
            return "[Object Not Found]"

        source = "<script>\n" + self._objects[name] \
            + "var fields_" + name + " = new Array()\n"
        i = 0
        for field in fields:
            source += "fields_" + name + "[" + str(i) + "] = " \
                + '"' + str(field).replace('"', r'\"') + "\";\n"
            i += 1
        source += "document.writeln(RSOBJ_" + name + "(fields_" + name + "))" \
            + "</script>"
        return source

bot = rivescript.RiveScript()
bot.set_handler("javascript", JSObject())
bot.load_file("javascript.rs")
bot.sort_replies()
while True:
    msg = raw_input("You> ")
    reply = bot.reply("localuser", msg)
    print "Bot>", reply
