# JSON Server

This example demonstrates embedding RiveScript in a Python web app,
accessible via a JSON endpoint.

This uses Flask to create a super simple web server that accepts JSON POST
requests to `/reply` and responds with JSON output.

## Run the Example

Open a shell into the `eg/json-server` directory. It's recommended to use a
virtualenv when working with Python apps, so these example steps assume this
is the case.

```bash
$ cd eg/json-server

# Make a virtualenv with virtualenvwrapper
$ mkvirtualenv json-test

# Install the requirements for this test app
(json-test)$ pip install -r requirements.txt

# And run it!
(json-test)$ python server.py
 * Running on http://0.0.0.0:5000/ (Press CTRL+C to quit)
```

And then from another terminal, you can use `curl` to test the JSON endpoint for
the chatbot. Or, you can use your favorite REST client.

## API Documentation

This simple Flask server only has one useful endpoint: `POST /reply`. All
other endpoints will return simple usage instructions (basically, a `curl`
command that you can paste into a terminal window).

### POST /reply

**Parameters (`application/json`):**

```json
{
	"username": "Soandso",
	"message": "Hello, bot!",
	"vars": {
		"name": "Soandso",
		"age": "10"
	}
}
```

The required parameters are `username` and `message`. You can provide `vars` to
send along user variables.

**Response:**

```json
{
	"status": "ok",
	"reply": "Hello human!",
	"vars": {
		"topic": "random",
		"name": "Soandso",
		"age": "10",
		"__history__": {},
		"__lastmatch__": "hello bot"
	}
}
```

The response includes `status` ("ok" or "error"), `reply` which is the bot's
response, and `vars` which are the user variables. To keep state between
requests, you should send *back* the `vars` data with the following request.
For example if the first request said "my name is soandso", `vars.name` will
be "Soandso" in the response. Passing the same `vars` back with the next
request will cause the bot to "remember" the name, and be able to keep track of
the user over multiple requests.

In case of error, a `message` key will contain the error message.

## Example Output

```bash
$ curl -i \
     -H "Content-Type: application/json" \
     -X POST -d '{"message": "Hello bot", "vars": {"name": "Soandso"}, "username": "soandso"}' \
     http://localhost:5000/reply
HTTP/1.0 200 OK
Content-Type: application/json
Content-Length: 708
Server: Werkzeug/0.11.3 Python/2.7.9
Date: Fri, 22 Jan 2016 21:48:43 GMT

{
  "reply": "How do you do. Please state your problem.",
  "status": "ok",
  "vars": {
    "__history__": {
      "input": [
        "hello bot",
        "undefined",
        "undefined",
        "undefined",
        "undefined",
        "undefined",
        "undefined",
        "undefined",
        "undefined"
      ],
      "reply": [
        "How do you do. Please state your problem.",
        "undefined",
        "undefined",
        "undefined",
        "undefined",
        "undefined",
        "undefined",
        "undefined",
        "undefined"
      ]
    },
    "__lastmatch__": "(hello|hi|hey|howdy|hola|hai|yo) [*]",
    "name": "Soandso",
    "topic": "random"
  }
}
```
