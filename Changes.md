Revision history for the Python package RiveScript.

1.12.3  Jul 8 2016
  - Fix the Python object macro handler to use `six.text_type` on the return
    value, allowing Python 2 objects to return Unicode strings.

1.12.2  May 31 2016
  - Fix a couple of bugs with `set_uservars()`.

1.12.1  May 31 2016
  - Added API functions: `get_global(name)`, `get_variable(name)`, and
    `set_uservars(user || dict[, dict])` -- the latter is for setting many
    variables for a user at once, or for setting many variables for many users.
    Refer to the API documentation for details.

1.12.0  May 10 2016
  - Add support for nested arrays, like `!array colors = @rgb white black`
    (PR #22)

1.10.0  Feb 16 2016
  - Add configurable `unicode_punctuation` attribute to strip out punctuation
    when running in UTF-8 mode.

1.8.1  Nov 19 2015
  - Add `@` to the list of characters that disqualifies a trigger from being
    considered "atomic"

1.8.0  Oct 10 2015
  - New algorithm for handling variable tags (<get>, <set>, <add>, <sub>,
    <mult>, <div>, <bot> and <env>) that allows for iterative nesting of
    these tags (for example, <set copy=<get orig>> will work now).
  - Fix sorting algorithm, so triggers with matching word counts will be
    sorted by length descending.
  - stream() function can accept a multiline string instead of an array
  - Speed optimization by precompiling as many regexps as possible (what was
    especially helpful was to precompile substitution and simple trigger
    regexps), taking the time-to-reply for the default brain from ~0.19s down
    to ~0.04s
  - Add support for `! local concat` option to override concatenation mode
    (file scoped)
  - Fix the regexp used when matching optionals so that the triggers don't match
    on inputs where they shouldn't. (RiveScript-JS issue #46)

1.06  Nov 25 2014
  - Change package name from python-rivescript to simply rivescript.
  - Change from the GPLv2 license to the MIT license.
  - Add compatibility with Python 3.
  - Add Unicode support for RiveScript documents.
  - Prefer the .rive extension for RS documents over the old .rs extension.
  - Track filenames and line numbers when parsing RiveScript documents.
  - Add Perl object handler example.
  - Add current_user() method accessible from inside an object macro.
  - Add unit tests.
  - Add deparse() function that dumps the active memory state of the bot.
  - Add write() method that writes the active memory state back to disk as a
    .rive file (uses deparse()).
  - Bugfix with substitution placeholders.
  - Bugfix with the <input> and <reply> tags.

1.01  May 20 2013
  - Small bugfix in _rot13 that caused crashes under certain circumstances.
  - Small bugfix regarding the {weight} tag and atomic triggers.
  - Restructure the RiveScript library (move rivescript.py into a package
    folder named 'rivescript', separate the interactive mode code into
    interactive.py)

1.00  Apr 22 2012
  - Initial version of rivescript.py
