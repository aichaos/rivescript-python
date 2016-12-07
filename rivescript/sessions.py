# RiveScript-Python
#
# This code is released under the MIT License.
# See the "LICENSE" file for more information.
#
# https://www.rivescript.com/

from __future__ import unicode_literals
import copy

class SessionManager(object):
    """Base class for session management for RiveScript.

    The session manager keeps track of getting and setting user variables,
    for example when the ``<set>`` or ``<get>`` tags are used in RiveScript
    or when the API functions like ``set_uservar()`` are called.

    By default RiveScript stores user sessions in memory and provides methods
    to export and import them (e.g. to persist them when the bot shuts down
    so they can be reloaded). If you'd prefer a more 'active' session storage,
    for example one that puts user variables into a database or cache, you can
    create your own session manager that extends this class and implements its
    functions.

    See the ``eg/sessions`` example from the source of rivescript-python at
    https://github.com/aichaos/rivescript-python for an example.

    The constructor takes no required parameters. You can feel free to define
    ``__init__()`` however you need to.
    """

    def set(self, username, args):
        """Set variables for a user.

        Args:
            username (str): The username to set variables for.
            args (dict): Key/value pairs of variables to set for the user.
                The values are usually strings, but they can be other types
                as well (e.g. arrays or other dicts) for some internal data
                structures such as input/reply history. A value of ``NoneType``
                should indicate that the key should be deleted from the session
                store.
        """
        raise NotImplementedError

    def get(self, username, key):
        """Retrieve a stored variable for a user.

        If the user doesn't exist, this should return ``None``. If the user
        *does* exist, but the key does not, this should return the
        string value ``"undefined"``.

        Args:
            username (str): The username to retrieve variables for.
            key (str): The specific variable name to retrieve.

        Returns:
            str: The value of the requested key, "undefined", or ``NoneType``.
        """
        raise NotImplementedError

    def get_any(self, username):
        """Retrieve all stored variables for a user.

        If the user doesn't exist, this should return ``None``.

        Args:
            username (str): The username to retrieve variables for.

        Returns:
            dict: Key/value pairs of all stored data for the user, or ``NoneType``.
        """
        raise NotImplementedError

    def get_all(self):
        """Retrieve all variables about all users.

        This should return a dict of dicts, where the top level keys are the
        usernames of every user your bot has data for, and the values are dicts
        of key/value pairs of those users. For example::

            { "user1": {
                "topic": "random",
                "name": "Alice",
                },
              "user2": {
                "topic": "random",
                "name": "Bob",
                },
            }

        Returns:
            dict
        """
        raise NotImplementedError

    def reset(self, username):
        """Reset all variables stored about a particular user.

        Args:
            username (str): The username to flush all data for.
        """
        raise NotImplementedError

    def reset_all(self):
        """Reset all variables for all users."""
        raise NotImplementedError

    def freeze(self, username):
        """Make a snapshot of the user's variables.

        This should clone and store a snapshot of all stored variables for the
        user, so that they can later be restored with ``thaw()``. This
        implements the RiveScript ``freeze_uservars()`` method.

        Args:
            username (str): The username to freeze variables for.
        """
        raise NotImplementedError

    def thaw(self, username, action="thaw"):
        """Restore the frozen snapshot of variables for a user.

        This should replace *all* of a user's variables with the frozen copy
        that was snapshotted with ``freeze()``. If there are no frozen
        variables, this function should be a no-op (maybe issue a warning?)

        Args:
            username (str): The username to restore variables for.
            action (str):
                An action to perform on the variables. Valid options are:

                * ``thaw``: Restore the variables and delete the frozen copy (default).
                * ``discard``: Don't restore the variables, just delete the frozen copy.
                * ``keep``: Restore the variables and keep the copy still.
        """
        raise NotImplementedError

    def default_session(self):
        """The default session data for a new user.

        You do not need to override this function. This returns a ``dict`` with
        the default key/value pairs for new sessions. By default, the
        session variables are as follows::

            {
                "topic": "random"
            }

        Returns:
            dict: A dict of default key/value pairs for new user sessions.
        """
        return dict(
            topic="random",
        )

class MemorySessionStorage(SessionManager):
    """The default in-memory session store for RiveScript.

    This session manager keeps all user and state information in system
    memory and doesn't persist anything to disk by default. This is suitable
    for many simple use cases. User variables can be persisted and reloaded
    from disk by using the RiveScript API functions ``get_uservars()`` and
    ``set_uservars()`` -- for example, you can get export all user variables
    and save them to disk as a JSON file when your program shuts down, and on
    its next startup, read the JSON file from disk and use ``set_uservars()``
    to put them back into the in-memory session manager.

    If you'd like to implement your own session manager, for example to use
    a database to store/retrieve user variables, you should extend the base
    ``SessionManager`` class and implement all of its functions.

    Parameters:
        warn (function): A function to be called with an error message to
            notify when one of the functions fails due to a user not existing.
            If not provided, then no warnings will be emitted from this module.
    """

    def __init__(self, warn=None, *args, **kwargs):
        self._fwarn = warn
        self._users = {}
        self._frozen = {}

    def _warn(self, *args, **kwargs):
        if self._fwarn is not None:
            self._fwarn(*args, **kwargs)

    def set(self, username, vars):
        if not username in self._users:
            self._users[username] = self.default_session()
        for key, value in vars.items():
            self._users[username][key] = value 

    def get(self, username, key):
        if not username in self._users:
            return None
        return self._users[username].get(key, "undefined")

    def get_any(self, username):
        if not username in self._users:
            return None
        return copy.deepcopy(self._users[username])

    def get_all(self):
        return copy.deepcopy(self._users)

    def reset(self, username):
        del self._users[username]

    def reset_all(self):
        self._users = {}

    def freeze(self, username):
        if username in self._users:
            self._frozen[username] = copy.deepcopy(self._users[username])
        else:
            self._warn("Can't freeze vars for user " + username + ": not found!")

    def thaw(self, username, action="thaw"):
        if username in self._frozen:
            # What are we doing?
            if action == "thaw":
                # Thawing them out.
                self._users[username] = copy.deepcopy(self._frozen[username])
                del self._frozen[username]
            elif action == "discard":
                # Just discard the frozen copy.
                del self._frozen[username]
            elif action == "keep":
                # Keep the frozen copy afterward.
                self._users[username] = copy.deepcopy(self._frozen[username])
            else:
                self._warn("Unsupported thaw action")
        else:
            self._warn("Can't thaw vars for user " + username + ": not found!")

class NullSessionStorage(SessionManager):
    """The null session manager doesn't store any user variables.

    This is used by the unit tests and isn't practical for real world usage,
    as the bot would be completely unable to remember any user variables or
    history.
    """
    def set(self, *args, **kwargs):
        pass

    def get(self, *args, **kwargs):
        return "undefined"

    def get_any(self, *args, **kwargs):
        return {}

    def get_all(self, *args, **kwargs):
        return {}

    def reset(self, *args, **kwargs):
        pass

    def reset_all(self, *args, **kwargs):
        pass

    def freeze(self, *args, **kwargs):
        pass

    def thaw(self, *args, **kwargs):
        pass
