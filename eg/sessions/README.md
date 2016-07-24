# Session Storage Example

By default RiveScript stores all user variables and state in memory, with no
automatic persistence to disk when the bot exits and restarts. RiveScript does
provide functions to export and import user variables in bulk so that you can
manually store and reload data, but an alternative is to use a third party
session storage driver.

The example bot at `redis-bot.py` uses a [Redis cache](http://redis.io/) to
store user variables. To run the example you'll need to install and start a
Redis server.

## Setup

```bash
###
# 1. Install Redis
###

# Fedora users:
sudo dnf install redis

# RHEL and CentOS <= 7
sudo yum install redis

# Debian/Ubuntu
sudo apt-get install redis-server

###
# 2. Start the Redis server
###

# Either do this to start it in a terminal window:
redis-server

# Or enable/start it with systemd.
sudo systemctl enable redis.service
sudo systemctl start redis.service

###
# 3. Run this example bot.
###

pip install -r requirements.txt
python redis_bot.py
```

## Example Output

```
% python redis_bot.py
RiveScript Redis Session Storage Example

This example uses a Redis server to store user variables. For the sake of the
example, choose a username to store your variables under. You can re-run this
script with the same username (or a different one!) and verify that your
variables are kept around!

Type '/quit' to quit.

What is your username? kirsle
You> Hello bot.
Bot> How do you do. Please state your problem.
You> My name is Noah.
Bot> Noah, nice to meet you.
You> Who am I?
Bot> You told me your name is Noah.
You> /quit

% python redis_bot.py
RiveScript Redis Session Storage Example

This example uses a Redis server to store user variables. For the sake of the
example, choose a username to store your variables under. You can re-run this
script with the same username (or a different one!) and verify that your
variables are kept around!

Type '/quit' to quit.

What is your username? kirsle
You> What's my name?
Bot> Your name is Noah.
You> /quit
```

And the Redis cache can be verified via the `redis-cli` command:

```
% redis-cli
127.0.0.1:6379> keys *
1) "rs-users/kirsle"
127.0.0.1:6379> get rs-users/kirsle
...redacted large JSON blob...
```
