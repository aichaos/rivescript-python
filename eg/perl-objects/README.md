# Perl Object Macros

This example demonstrates how a Python RiveScript bot may support Perl as a
language for executing object macros.

It essentially works by executing a Perl script (`accomplice.pl`) in a Perl
interpreter, passing along all the necessary information about the object macro
request, and getting the output from it.

This is a tongue-in-cheek example and probably isn't safe to use in production.
