#!/usr/bin/env python

# Manipulate sys.path to be able to import rivescript from this local git
# repository.
import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))

from flask import Flask, request, Response, jsonify
import json
from rivescript import RiveScript

# Set up the RiveScript bot. This loads the replies from `/eg/brain` of the
# git repository.
bot = RiveScript()
bot.load_directory(
    os.path.join(os.path.dirname(__file__), "..", "brain")
)
bot.sort_replies()

app = Flask(__name__)

@app.route("/reply", methods=["POST"])
def reply():
    """Fetch a reply from RiveScript.

    Parameters (JSON):
    * username
    * message
    * vars
    """
    params = request.json
    if not params:
        return jsonify({
            "status": "error",
            "error": "Request must be of the application/json type!",
        })

    username = params.get("username")
    message  = params.get("message")
    uservars = params.get("vars", dict())

    # Make sure the required params are present.
    if username is None or message is None:
        return jsonify({
            "status": "error",
            "error": "username and message are required keys",
        })

    # Copy and user vars from the post into RiveScript.
    if type(uservars) is dict:
        for key, value in uservars.items():
            bot.set_uservar(username, key, value)

    # Get a reply from the bot.
    reply = bot.reply(username, message)

    # Get all the user's vars back out of the bot to include in the response.
    uservars = bot.get_uservars(username)

    # Send the response.
    return jsonify({
        "status": "ok",
        "reply": reply,
        "vars": uservars,
    })

@app.route("/")
@app.route("/<path:path>")
def index(path=None):
    """On all other routes, just return an example `curl` command."""
    payload = {
        "username": "soandso",
        "message": "Hello bot",
        "vars": {
            "name": "Soandso",
        }
    }
    return Response(r"""Usage: curl -i \
    -H "Content-Type: application/json" \
    -X POST -d '{}' \
    http://localhost:5000/reply""".format(json.dumps(payload)),
    mimetype="text/plain")

if __name__ == "__main__":
    app.run(host='0.0.0.0', debug=True)
