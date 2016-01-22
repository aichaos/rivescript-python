# Twilio Example

This example uses the [Twilio Cloud Communications Platform](https://www.twilio.com/)
and creates a RiveScript bot that can communicate with users via SMS.

![Screenshot](https://raw.github.com/aichaos/rivescript-python/master/eg/twilio/screenshot.png)

# Setup Steps

## Running the Flask App

This app example is designed to be run from within the git project directory for
`rivescript-python`. Here are the shell commands needed to run this example app.

It's recommended to use a [virtualenv](https://virtualenv.readthedocs.org/en/latest/)
when working with Python apps. The following instructions assume you're in a
Python 3 environment, which includes `pyvenv` as a built-in `virtualenv`-like
system. For Python 2 or earlier versions of Python 3, install virtualenv first
and substitute all of the `venv` commands with `virtualenv`.

```bash
# Clone the git repository if you don't already have it.
$ git clone https://github.com/aichaos/rivescript-python && cd rivescript-python

# Create a virtualenv and install rivescript's dependencies.
$ pyvenv .env
$ source .env/bin/activate
(.env)$ pip install -r requirements.txt

# Go into the twilio example and install its requirements, too.
(.env)$ cd eg/twilio
(.env)$ pip install -r requirements.txt

# Run the Flask app
(.env)$ python app.py
* Running on http://0.0.0.0:5000/ (Press CTRL+C to quit)
```

Test that the app basically works by requesting the following URL from your
server in your web browser (substituting `yourserver.com` with your server's
domain or IP address):

`http://yourserver.com:5000/twilio?From=123456789&Body=hello`

You should get a response from the bot, such as "How do you do. Please state
your problem."

You can test it on the command line from a different terminal session on your
server, too:

```bash
$ curl 'http://127.0.0.1:5000/twilio?From=123456789&Body=hello'
<?xml version="1.0" encoding="UTF-8"?><Response><Message><Body>Hi. What seems
to be your problem?</Body></Message></Response>
```

If this is working, continue to the next step.

## Set up Twilio

If you don't already have one, you need to create an account on Twilio. You can
use a free trial account for testing, which is enough to support SMS messages.

Set up a Voice Number if you don't already have one, and go to the
[Phone Numbers](https://www.twilio.com/user/account/voice/phone-numbers) tab in
your Twilio console.

Click on your phone number, go to the Messaging tab, and edit the "Request URL"
to point to the external URL of your Twilio example app. For example:

`http://yourserver.com:5000/twilio`

Leave the method as "HTTP POST".

After clicking "Save", test it by sending an SMS message to your Twilio phone
number. If you're watching the Flask app, you should see a POST request to your
`/twilio` endpoint and moments later, your Twilio number should reply to your
message.

# Productionize

Flask isn't very well designed to be run "in production" by just doing
"python app.py"; Flask's internal web server is only to be used for local
development and testing.

See [Deployment Options](http://flask.pocoo.org/docs/0.10/deploying/) in the
Flask documentation and pick an option that suits you.
