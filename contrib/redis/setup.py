# rivescript-python setup.py

import rivescript_redis
from setuptools import setup

setup(
    name             = 'rivescript_redis',
    version          = rivescript_redis.__version__,
    description      = 'Redis driver for RiveScript',
    long_description = 'Stores user variables for RiveScript in a Redis cache',
    author           = 'Noah Petherbridge',
    author_email     = 'root@kirsle.net',
    url              = 'https://github.com/aichaos/rivescript-python',
    license          = 'MIT',
    py_modules       = ['rivescript_redis'],
    keywords         = ['rivescript'],
    classifiers      = [
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 3',
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Topic :: Scientific/Engineering :: Artificial Intelligence',
    ],
    install_requires = [ 'setuptools', 'redis', 'rivescript' ],
)

# vim:expandtab
