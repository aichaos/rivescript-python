# rivescript-python setup.py

import rivescript
from setuptools import setup

setup(
    name             = 'rivescript',
    version          = rivescript.__version__,
    description      = 'A Chatterbot Scripting Language',
    long_description = 'A scripting language to make it easy to write responses for a chatterbot.',
    author           = 'Noah Petherbridge',
    author_email     = 'root@kirsle.net',
    url              = 'https://github.com/aichaos/rivescript-python',
    license          = 'MIT',
    packages         = ['rivescript'],
    keywords         = ['bot', 'chatbot', 'chatterbot', 'ai', 'aiml',
                        'chatscript', 'buddyscript'],
    classifiers      = [
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python',
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'Topic :: Scientific/Engineering :: Artificial Intelligence',
    ],
    install_requires = [ 'setuptools', 'six' ],
)

# vim:expandtab
