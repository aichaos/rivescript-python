# RiveScript Parser Example

The RiveScript parser was broken out into its own stand-alone module usable by
third party developers, and this is an example of how to use it.

The bare minimum code to use the RiveScript parser are as follows:

```python
from rivescript.parser import Parser

# Instantiate it.
p = Parser()

# And parse some RiveScript code!
ast = p.parse("any-file-name.rive", [
    "+ hello bot",
    "- Hello human!",
])
```

The `Parser.parse()` function requires a file name (used only for syntax
reporting purposes) and an array of lines of source code to parse.

## Running the Example

```bash
# Simply run it! It will parse and dump ../brain/clients.rive by default.
% python parse.py

# Or give it the name of a different RiveScript file.
% python parse.py ../brain/eliza.rive

# Or enable debug logging.
% env PARSER_DEBUG=1 python parse.py ../brain/begin.rive

# (For the Windows/Command Prompt users)
> set PARSER_DEBUG=1
> python parse.py ../brain/myself.rive
```

The parse script will parse the RiveScript file given on the command line,
and dump its "abstract syntax tree" as JSON to the standard output so you can
see what the data structure looks like.

Check the source code of `parse.py` for the details. The environment variable
`PARSER_DEBUG` is something the example script uses, not the underlying
`rivescript.parser` module; debugging is made possible by using the `on_debug`
and `on_warn` arguments to the Parser constructor.

## Example Output

`python parse.py ../brain/admin.rive`

```json
{
  "begin": {
    "array": {},
    "global": {},
    "person": {},
    "sub": {},
    "var": {}
  },
  "objects": [
    {
      "code": [
        "\tmy ($rs) = @_;\n",
        "\t# Shut down.\n",
        "\texit(0);\n"
      ],
      "language": "perl",
      "name": "shutdown"
    },
    {
      "code": [
        "\t# Shut down\n",
        "\tquit()\n"
      ],
      "language": "python",
      "name": "shutdown"
    }
  ],
  "topics": {
    "random": {
      "includes": {},
      "inherits": {},
      "triggers": [
        {
          "condition": [
            "<id> eq <bot master> => Shutting down... <call>shutdown</call>"
          ],
          "previous": null,
          "redirect": null,
          "reply": [
            "{@botmaster only}"
          ],
          "trigger": "shutdown{weight=10000}"
        },
        {
          "condition": [],
          "previous": null,
          "redirect": null,
          "reply": [
            "This command can only be used by my botmaster. <id> != <bot master>"
          ],
          "trigger": "botmaster only"
        }
      ]
    }
  }
}
```
