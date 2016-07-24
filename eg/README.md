# Examples

These directories include example snippets for how to do various things with
RiveScript-Python.

## RiveScript Example

* [brain](brain/) - The standard default RiveScript brain (`.rive` files) that
  implements an Eliza-like bot with added triggers to demonstrate other features
  of RiveScript.

## Client Examples

* [json-server](json-server/) - A minimal Flask web server that makes a
  RiveScript bot available at a JSON POST endpoint.
* [twilio](twilio/) - An example that uses the Twilio SMS API to create a bot
  that can receive SMS text messages from users and reply to them using
  RiveScript.

## Code Snippets

* [sessions](sessions/) - Demonstrates replacing the default in-memory session
  storage with ones that support persistent back-end storage systems.
* [parser](parser/) - Use the `rivescript.parser` module to parse RiveScript
  code yourself.
* [js-objects](js-objects/) - Demonstrates adding JavaScript object macro
  support to RiveScript-Python. This example assumes a Python RiveScript bot is
  serving its responses via a web front-end, so that the JS macros are being
  executed in the user's browser via `<script>` tags.
* [perl-objects](perl-objects/) - Demonstrates adding Perl object macro support
  to RiveScript-Python. This works by running a Perl script, which uses the Perl
  version of RiveScript, and passing essential data about the object call into
  the Perl script and retrieving the output.
