# Changes

Revision history for the Python package RiveScript.

## 1.15.0 - Mar 29 2020

This release provides a major (~5x) speedup for RiveScripts that have
a large number of substitutions, and also fixes the following issues:

- Add a `prepare_brain_transplant` method to clear the RiveScript brain
  in preparation to load in a new one, while optionally preserving
  much of the current state (enh #81)
- Implement the `trigger_info` method (bug #120)
- Fix the issue of a "=" appearing in a variable value (bug #130)
- Allow nested brackets (bug #132)
- Fix trigger sorting to only count the existance of stars, optionals,
  etc. instead of how many there are in a trigger (bug #133)
- Fix the debug message for incomment (bug #138)
- Fix substitutions if they occur more than 3 times on a line (bug #140)
- Fix crash in `set_substitution` method (bug #142)
- Fix issue in `set_person` method (bug #143)
- Significantly improve code coverage of tests (add `test_coverage.py`)

Dropped support for Python 2.7 as it this language version has reached
its end-of-life date. Minimum Python version supported is now 3.6+

## 1.14.9 - Sept 21 2017

This release fixes some regular expressions and adds better Unicode
compatibility for trigger matching.

- Fix the regexp that matches `{weight}` tags in replies to use `re.search()`
  instead of `re.match()`. This ensures that random replies are chosen with the
  correct weighting applied (bug #102; PR #106)
- Fix the way arrays are interpolated into triggers so that array names are
  now allowed to contain underscores (bug #101; PR #107)
- Fix Unicode handling in regular expressions by using the `re.UNICODE` flag.
  This allows for a trigger containing optionals, like `[*]`, to match
  correctly when adjacent to Unicode symbols such as umlauts (bug #37; PR #108)

## 1.14.8 - Sept 5 2017

This release focuses on bug fixes and backwards compatible improvements.

- Improvements to the new trigger sorting algorithm:
  - Triggers containing no text (wildcards only) are sorted nearer to the end
    (bug #94)
- Trigger components containing an empty string between pipes (e.g. `[|]`) now
  raises a syntax error at parsing time (bug #87)
- Fix the parsing of `^` when used on a `+Trigger` not being fully evaluated
  before syntax checking for the trigger was done (bug #86)
- Remove extra space characters inside optionals (bug #98)
- Improve the syntax checker by having it raise errors when certain "tag
  characters" are mismatched or opened and closed in the wrong order -- for
  example `{<}>` (PR #103)
- Fix the `deparse()` and `write()` functions so they work again with the
  latest version of RiveScript (bug #76)

## 1.14.7 - May 19 2017

- Various fixes and improvements that catch RiveScript-Python up with the other
  implementations, to pass the RiveScript Test Suite (PR #89):
  - Implement arrays in replies -- so you could write a reply like
    `My favorite color is (@colors)` and the array gets expanded to a random
    item from the `!array` by the same name.
  - Fix the regexp for `{weight}` tag removal so that it still works if you
    include extra spaces on either end of the tag.
  - Fix the `_` wildcard to allow matching Unicode letters.
  - Fix division with the `<div>` tag to use integer division for Python 3.
- Improvements to the trigger sorting algorithm:
  - Add special handling so that a trigger of `[*]` gets sorted above the
    usual catch-all trigger of `*` (PR #92)
  - Fix a logic bug with bitwise operators for handling the case that a trigger
    contains `*` wildcards but does not contain any optionals or wildcards of
    different types (bug #90, PR #91)

## 1.14.6 - Mar 23 2017

- Fix regexp for validating RiveScript syntax to use `re.search` instead of
  `re.match` (bug #82).
- Allow object macros to contain capital letters in their names (PR #83).

## 1.14.5 - Feb 20 2017

- Bugfix when storing the user's `last_match` variable when a `%Previous` is
  active (it was storing a regexp object and not a string), to help third party
  session drivers (e.g. Redis) to work.

## 1.14.4 - Dec 14 2016

- Fix the `last_match()` function so that it returns `None` when there was no
  match instead of `"undefined"` (PR #63).
- Strip leading and trailing whitespace from user messages, and consolidate
  repeated whitespace into a single space character (PR #62).

## 1.14.3 - Dec 8 2016

- Fix sorting algorithm for triggers with `%Previous`, making their sort order
  deterministic and correct regardless of the order they appeared in the
  source file (PR #60; bug #59).
- Fix a possible crash when interpolating a `<star>` tag when the trigger
  had captured no stars. In this cases the `<star>` tag will become the string
  `"None"`; it is a user error that this situation arises anyway and this fix
  just prevents Python from crashing (bugs #51 and #54).
- Fix a possible crash when calling `random.choice` on an empty list by
  wrapping it in a safety function at `rivescript.utils.random_choice`
  (bug #36).
- Better error reporting on the JSON Interactive Mode: if there is an
  exception raised when decoding the input JSON, the output JSON now contains
  an `error` key with the text of the exception to help diagnose what went
  wrong.

## 1.14.2 - Oct 18 2016

- Fix numeric tags like `<add>` raising a `TypeError` exception.

## 1.14.1 - Aug 9 2016

- Fix a regression when handling Unicode strings under Python 2 (bug #40).

## 1.14.0 - Jul 23 2016

- Make the session manager pluggable and replaceable. RiveScript still uses
  an in-memory store for user variables, but this can be swapped out with a
  replacement that puts user variables somewhere else, like Redis or MySQL.
  The constructor accepts a `session_manager` parameter to use your own
  session manager based on the `rivescript.sessions.SessionManager` class.
- Make the RiveScript Parser module (`rivescript.parser`) more developer
  friendly by removing the parent RiveScript module as a dependency. The
  parser can be used as a stand-alone module if all you want to do is parse
  and validate RiveScript code.
- The `log` parameter to the constructor may now be an already opened file
  handle (opened in write or append mode) instead of a string, if you already
  have a file handle ready.
- Add two examples to the `eg` directory:
  - `eg/sessions` replaces the in-memory session store with one that uses
    a Redis cache instead.
  - `eg/parser` shows how to use the RiveScript Parser module.
- Fix a bug where atomic triggers that contain a `{weight}` tag were unable
  to be matched properly.
- Reorganize the unit tests into many smaller files instead of one large one.

## 1.13.0 - Jul 21 2016

- Restructure the code to keep it on par with the JavaScript and Go versions:
  - `rivescript.parser` now contains all the parsing code:
    `parse()` and `check_syntax()` are moved here.
  - Triggers are stored internally in only one place now, like in the
    JavaScript and Go versions. This makes some internal mappings simpler as
    they now point to common references and don't duplicate data in memory.
  - **Note:** Most of the new `rivescript.*` modules are still
    private-use-only, even though many internal functions lost their
    underscore prefixes. You should still only use the API functions exposed
    by `rivescript.rivescript` or what is exported by the top level package.
    The `rivescript.parser` API will be more public-facing in the future to
    help with third party integrations (currently it still relies on a Python
    object with methods `_say` and `_warn`).
- Refactor the RiveScript interactive mode (`rivescript.interactive`) to use
  argparse instead of getopt and add a pretty ASCII logo.
- Add `shell.py` as a possibly easier-to-access (and certainly
  easier-to-discover) shortcut to running RiveScript's interactive mode.
  It accepts all the same options and works the same as before.

## 1.12.3 - Jul 8 2016

- Fix the Python object macro handler to use `six.text_type` on the return
  value, allowing Python 2 objects to return Unicode strings.

## 1.12.2 - May 31 2016

- Fix a couple of bugs with `set_uservars()`.

## 1.12.1 - May 31 2016

- Added API functions: `get_global(name)`, `get_variable(name)`, and
  `set_uservars(user || dict[, dict])` -- the latter is for setting many
  variables for a user at once, or for setting many variables for many users.
  Refer to the API documentation for details.

## 1.12.0 - May 10 2016

- Add support for nested arrays, like `!array colors = @rgb white black`
  (PR #22)

## 1.10.0 - Feb 16 2016

- Add configurable `unicode_punctuation` attribute to strip out punctuation
  when running in UTF-8 mode.

## 1.8.1 - Nov 19 2015

- Add `@` to the list of characters that disqualifies a trigger from being
  considered "atomic"

## 1.8.0 - Oct 10 2015

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

## 1.06 - Nov 25 2014

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

## 1.01 - May 20 2013

- Small bugfix in \_rot13 that caused crashes under certain circumstances.
- Small bugfix regarding the {weight} tag and atomic triggers.
- Restructure the RiveScript library (move rivescript.py into a package
  folder named 'rivescript', separate the interactive mode code into
  interactive.py)

## 1.00 - Apr 22 2012

- Initial version of rivescript.py
