# Redis Sessions for RiveScript

This module installs support for using a [Redis cache](https://redis.io/) to
store user variables for RiveScript.

```bash
pip install rivescript-redis
```

By default, RiveScript keeps user variables in an in-memory dictionary. This
driver allows for using a Redis cache instead. All user variables will then be
persisted to Redis automatically, which enables the bot to remember users after
a reboot.

## Quick Start

```python
from rivescript import RiveScript
from rivescript_redis import RedisSessionManager

# Initialize RiveScript like normal but give it the RedisSessionManager.
bot = RiveScript(
    session_manager=RedisSessionManager(
        # You can customize the key prefix: this is the default. Be sure to
        # include a separator like '/' at the end so the keys end up looking
        # like e.g. 'rivescript/username'
        prefix='rivescript/',

        # All other options are passed directly through to redis.StrictRedis()
        host='localhost',
        port=6379,
        db=0,
    ),
)

bot.load_directory("eg/brain")
bot.sort_replies()

# Get a reply. The user variables for 'alice' would be persisted in Redis
# at the (default) key 'rivescript/alice'
print(bot.reply("alice", "Hello robot!"))
```

## Example

An example bot that uses this driver can be found in the
[`eg/sessions`](https://github.com/aichaos/rivescript-python/tree/master/eg/sessions)
directory of the `rivescript-python` project.

## See Also

* Documentation for [redis-py](https://redis-py.readthedocs.io/en/latest/),
  the Redis client module used by this driver.

## License

This module is licensed under the same terms as RiveScript itself (MIT).
