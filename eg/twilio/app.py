#!/usr/bin/env python3

"""Example Twilio SMS chatbot for RiveScript.

See the accompanying README.md for instructions."""

# Manipulate sys.path to be able to import rivescript from this git repo.
# Otherwise you'd have to `pip install rivescript`
import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))

from flask import Flask, request, redirect
from rivescript import RiveScript
import twilio.twiml

# Set up the RiveScript bot. This loads the replies from "../brain", or,
# the "brain" folder in the "eg" folder of this git repository.
bot = RiveScript()
bot.load_directory(
    os.path.join(os.path.dirname(__file__), "..", "brain")
)
bot.sort_replies()

app = Flask(__name__)

@app.route("/twilio", methods=["GET", "POST"])
def hello_rivescript():
    """Receive an inbound SMS and send a reply from RiveScript."""

    from_number = request.values.get("From", "unknown")
    message     = request.values.get("Body")
    reply       = "(Internal error)"

    # Get a reply from RiveScript.
    if message:
        reply = bot.reply(from_number, message)

    # Send the response.
    resp = twilio.twiml.Response()
    resp.message(reply)
    return str(resp)

if __name__ == "__main__":
    app.run(host='0.0.0.0', debug=True)
