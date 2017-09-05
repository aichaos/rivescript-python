# RiveScript Deparse

This example purely consists of additional documentation and examples of the
`deparse()` method of RiveScript.

## Relevant Methods

* `rs.deparse()`

  This method exports the current in-memory representation of the RiveScript
  brain as a JSON-serializable data structure. See [Schema](#schema) for the
  format of this data structure.

* `rs.write(fh[, deparsed])`

  This method converts a data structure like the one from `deparse()` into plain
  text RiveScript source code and writes it to the file-like object ``fh``.

  By default this will use the current in-memory representation of the
  RiveScript brain. For example, if you loaded a directory of RiveScript files
  and then called `write()` you would get a large text blob that contains
  all the source code of all the files from that directory. Note, however, that
  the formatting of the original reply data might be lost because the output
  from `write()` is working backwards from the in-memory representation, so
  for example, comments in the original source code aren't preserved and places
  where `^Continue` was used will instead result in one single line of code
  in the output.

  If you pass in a data structure formatted the same way as the one `deparse()`
  returns, you can write that code instead. This way you could
  programmatically generate RiveScript data (for example, from a custom user
  interface for authoring bots) and convert it into valid RiveScript source code
  using this method.

## Schema

The data structure returned by `deparse()` looks like this, annotated:

```yaml
begin:
  global:   map of key/value pairs for `! global` global variable definitions
  var:      map of key/value pairs for `! var` bot variable definitions
  sub:      map of key/value pairs for `! sub` substitution definitions
  person:   map of key/value pairs for `! person` substitution definitions
  array:    map of `! array` names to arrays of their values
  triggers: array of trigger data (see below)
topics:     map of topic names -> array of trigger data under that topic
  $name: []
```

The trigger data is stored in arrays underneath `begin.triggers` (for those in
the `> begin` block) and `topics.$NAME` for triggers under a particular topic,
with the default topic being named "random".

Each trigger is an object with the following schema:

```yaml
trigger:   the plain text trigger
reply:     array of the plain text `-Reply` commands, or `[]`
condition: array of the plain text `*Condition` commands, or `[]`
redirect:  the text of the `@Redirect` command, or `null`
previous:  the text of the `%Previous` command, or `null`
```

## Examples

Here are some example code snippets that show what the deparsed data structure
looks like.

Python Code (`example.py`)

```python
from rivescript import RiveScript
import json

bot = RiveScript()
bot.load_file("example.rive")

dep = bot.deparse()
print(json.dumps(dep, indent=2))
```

RiveScript Code (`example.rive`)

```rivescript
! version = 1.0

! var name = Aiden
! var age  = 5

! sub what's = what is

! array colors = red blue green yellow cyan magenta black white

> begin
  + request
  - {ok}
< begin

+ hello bot
- Hello human.

+ hi robot
@ hello bot

+ my name is *
- <set name=<formal>>Nice to meet you, <get name>.
- <set name=<formal>>Hello, <get name>.

+ what is my name
* <get name> != undefined => Your name is <get name>.
- You didn't tell me your name.

> topic game-global
  + help
  - How to play...
< topic

> topic game-room-1 inherits game-global
  + look
  - You're in a room labeled "1".
< topic

> object reverse javascript
  var msg = args.join(" ");
  return msg.split("").reverse().join("");
< object

+ say * in reverse
- <call>reverse <star></call>
```

JSON output:

```javascript
{
  "begin": {
    "global": {},
    "var": {
      "name": "Aiden",
      "age": "5"
    },
    "sub": {
      "what's": "what is"
    },
    "person": {},
    "array": {
      "colors": [
        "red",
        "blue",
        "green",
        "yellow",
        "cyan",
        "magenta",
        "black",
        "white"
      ]
    },
    "triggers": [
      {
        "trigger": "request",
        "reply": [
          "{ok}"
        ],
        "condition": [],
        "redirect": null,
        "previous": null
      }
    ]
  },
  "topics": {
    "random": {
      "triggers": [
        {
          "trigger": "hello bot",
          "reply": [
            "Hello human."
          ],
          "condition": [],
          "redirect": null,
          "previous": null
        },
        {
          "trigger": "hi robot",
          "reply": [],
          "condition": [],
          "redirect": "hello bot",
          "previous": null
        },
        {
          "trigger": "my name is *",
          "reply": [
            "<set name=<formal>>Nice to meet you, <get name>.",
            "<set name=<formal>>Hello, <get name>."
          ],
          "condition": [],
          "redirect": null,
          "previous": null
        },
        {
          "trigger": "what is my name",
          "reply": [
            "You didn't tell me your name."
          ],
          "condition": [
            "<get name> != undefined => Your name is <get name>."
          ],
          "redirect": null,
          "previous": null
        },
        {
          "trigger": "say * in reverse",
          "reply": [
            "<call>reverse <star></call>"
          ],
          "condition": [],
          "redirect": null,
          "previous": null
        }
      ],
      "includes": {},
      "inherits": {}
    },
    "game-global": {
      "triggers": [
        {
          "trigger": "help",
          "reply": [
            "How to play..."
          ],
          "condition": [],
          "redirect": null,
          "previous": null
        }
      ],
      "includes": {},
      "inherits": {}
    },
    "game-room-1": {
      "triggers": [
        {
          "trigger": "look",
          "reply": [
            "You're in a room labeled \"1\"."
          ],
          "condition": [],
          "redirect": null,
          "previous": null
        }
      ],
      "includes": {},
      "inherits": {
        "game-global": 1
      }
    }
  }
}
```
