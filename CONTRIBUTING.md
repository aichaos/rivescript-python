# Contributing

Interested in contributing to RiveScript? Great!

First, check the general contributing guidelines for RiveScript and its primary
implementations found at <http://www.rivescript.com/contributing> - in
particular, understand the goals and scope of the RiveScript language and the
style guide for the Python implementation.

# Quick Start

Fork, then clone the repo:

```bash
$ git clone git@github.com:your-username/rivescript-python.git
```

Make your code changes and test them by using the built-in interactive mode of
RiveScript, e.g. by running `python rivescript /path/to/brain`.

Make sure the unit tests still pass. I use Nosetests for the unit testing, so
you'll need to install that (you can install it in a virtualenv if it's easier)
and run the command `nosetests`.

Use `pyflakes` and clean up any error messages reported in the Python sources.

Push to your fork and [submit a pull request](https://github.com/kirsle/rivescript-python/compare/).

At this point you're waiting on me. I'm usually pretty quick to comment on pull
requests (within a few days) and I may suggest some changes or improvements
or alternatives.

Some things that will increase the chance that your pull request is accepted:

* Follow the style guide at <http://www.rivescript.com/contributing>
* Write a [good commit message](http://tbaggery.com/2008/04/19/a-note-about-git-commit-messages.html).
