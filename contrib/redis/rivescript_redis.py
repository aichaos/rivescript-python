# RiveScript-Python
#
# This code is released under the MIT License.
# See the "LICENSE" file for more information.
#
# https://www.rivescript.com/

from __future__ import unicode_literals
import json
import redis
from rivescript.sessions import SessionManager

__author__    = 'Noah Petherbridge'
__copyright__ = 'Copyright 2017, Noah Petherbridge'
__license__   = 'MIT'
__status__    = 'Beta'
__version__   = '0.1.0'

class RedisSessionManager(SessionManager):
    """A Redis powered session manager for RiveScript."""

    def __init__(self, prefix="rivescript/", *args, **kwargs):
        """Initialize the Redis session driver.

        Apart from the ``prefix`` parameter, all other options are passed
        directly to the underlying Redis constructor, ``redis.StrictRedis()``.
        See the documentation of redis-py for more information. Commonly used
        arguments are listed below for convenience.

        Args:
            prefix (string): the key to prefix all the Redis keys with. The
                default is ``rivescript/``, so that for a username of ``alice``
                the key would be ``rivescript/alice``.
            host (string): Hostname of the Redis server.
            port (int): Port number of the Redis server.
            db (int): Database number in Redis.
        """
        self.client = redis.StrictRedis(*args, **kwargs)
        self.prefix = prefix
        self.frozen = "frozen:" + prefix

    def _key(self, username, frozen=False):
        """Translate a username into a key for Redis."""
        if frozen:
            return self.frozen + username
        return self.prefix + username

    def _get_user(self, username):
        """Custom helper method to retrieve a user's data from Redis."""
        data = self.client.get(self._key(username))
        if data is None:
            return None
        return json.loads(data.decode())

    # The below functions implement the RiveScript SessionManager.

    def set(self, username, new_vars):
        data = self._get_user(username)
        if data is None:
            data = self.default_session()
        data.update(new_vars)
        self.client.set(self._key(username), json.dumps(data))

    def get(self, username, key):
        data = self._get_user(username)
        if data is None:
            return None
        return data.get(key, "undefined")

    def get_any(self, username):
        return self._get_user(username)

    def get_all(self):
        users = self.client.keys(self.prefix + "*")
        result = dict()
        for user in users:
            username = users.replace(self.prefix, "")
            result[username] = self._get_user(username)
        return result

    def reset(self, username):
        self.client.delete(self._key(username))

    def reset_all(self):
        users = self.client.keys(self.prefix + "*")
        for user in users:
            self.c.delete(user)

    def freeze(self, username):
        data = self._get_user(username)
        if data is not None:
            self.client.set(self._key(username, True), json.dumps(data))

    def thaw(self, username, action="thaw"):
        data = self.client.get(self.key(username, True))
        if data is not None:
            data = json.loads(data.decode())
            if action == "thaw":
                self.reset(username)
                self.set(username, data)
                self.c.delete(self.key(username, True))
            elif action == "discard":
                self.c.delete(self.key(username, True))
            elif action == "keep":
                self.reset(username)
                self.set(username, data)
            else:
                raise ValueError("unsupported thaw action")
