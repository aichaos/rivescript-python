# rivescript-python setup.py

import rivescript
from distutils.core import setup

setup(
    name             = 'python-rivescript',
    version          = rivescript.VERSION,
    description      = 'A Chatterbot Scripting Language',
    long_description = 'A scripting language to make it easy to write responses for a chatterbot.',
    author           = 'Noah Petherbridge',
    author_email     = 'root@kirsle.net',
    url              = 'https://github.com/kirsle/rivescript-python',
    license          = 'Dual licensed; GPLv2',
    py_modules       = ['rivescript'],
)

# vim:expandtab
