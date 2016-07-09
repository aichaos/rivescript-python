#!/usr/bin/python

from __future__ import print_function
import os
import sys
import json
import logging as log
log.basicConfig(format='%(levelname)s -- %(message)s', level=log.WARN)

# Setup sys.path to be able to import rivescript from this local git repo.
sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))

from rivescript import RiveScript

SCRIPT_DIR    =  os.path.join(os.path.dirname(__file__), '..', 'brain')
SESSION_FILE  =  os.path.join(os.path.dirname(__file__), 'sessions.json')

print('-' * 70)
print("""An example RiveScript bot which saves user sessions and lets
the user continue when the script is run again.

To see how it works, run the script with user name as the argument, eg:
`python example.py john` and enter the RPG demo by typing `rpg demo`.

After playing a while, exit the script (via /quit, Ctrl-C, Ctrl-D, etc.)
and run again to jump back to where you stopped in the Rive script. Then
start the script as a different user. You can also check the contents 
of `sessions.json` file once in a while to see session data.""")
print('-' * 70)


class SessionStore(object):
	"""Abstract SessionStore class."""
	def load(self, user):
		"""Load and return RiveSession object for a given user"""
		raise NotImplementedError('Subclass SessionStore and override load()')

	def save(self, session):
		"""Save session based on given RiveSession object"""
		raise NotImplementedError('Subclass SessionStore and override save()')


class SimpleSessionStore(SessionStore):
	"""Basic SessionStore implementation, reading/writing a single JSON file."""
	def __init__(self, file_name):
		super(SimpleSessionStore, self).__init__()
		self._file_name = file_name

	def load(self, user):
		"""Load session data from JSON file."""
		try:
			with file(self._file_name, 'rb') as sf:
				data = json.load(sf)
				if user in data:
					return RiveSession(user, data=data[user])
		except ValueError:
			log.warn("Malformed JSON data in file: {}".format(file_name))
		except IOError:
			# file not found, ignore
			pass

		return RiveSession(user)   # new (empty) session

	def save(self, session):
		"""Save session to JSON file, preserving other sessions (if any)."""
		alldata = {}
		try:
			with file(self._file_name, 'rb') as sf:
				alldata = json.load(sf)
		except ValueError:
			log.warn("Malformed JSON data in file: {}".format(file_name))
		except IOError:
			# file not found, ignore
			pass

		alldata[session._user] = session._data
		with file(self._file_name, 'wb') as sf:
			json.dump(alldata, sf, indent=4)


class RiveSession(object):
	"""User session object.

	Structure of session data:
	{
		'topic': 'topic/redirect',
		'vars' : {
			'name' : 'value',
			...
		}
	}
	"""
	def __init__(self, user, data={'vars':{}}):
		self._user = user
		self._data = data
	
	def set_topic(self, topic, redirect=None):
		self._data['topic'] = "{}/{}".format(topic, redirect) if redirect else topic

	def get_topic(self):
		return self._data['topic'] if 'topic' in self._data else None

  	def set_variable(self, name, value):
  		self._data['vars'][name] = value

  	def get_variable(self, name):
  		if 'name' in self._data['vars']:
  			return self._data['vars'][name]
  		else:
  			return None

  	def variables(self):
  		"""User variables iterator."""
  		for k, v in self._data['vars'].items():
  			yield k, v


class RiveBot(object):
	"""An example RiveScript bot using callbacks to manage user session data.

	This example assumes single user per RiveScript instance and as
	such it's suitable for use in stateless services (e.g. in web apps
	receiving webhooks). Just init, get reply and teardown. Of course,
	it will also work in RTM implementations with custom longer-lived 
	bot threads.

	Session state is persisted to a single JSON file. This wouldn't be 
	thread-safe in a concurrent environment (e.g. web server). In such
	case it would be recommended to subclass SessionStore and implement
	database persistence (preferably via one of great Python ORMs such
	as SQLAlchemy or peewee).
	"""
	def __init__(self, script_dir, user, ss, debug=False):
		self._user     = user
		self._redirect = None

		# init RiveScript
		self._rs = RiveScript(debug=debug)
		self._rs.load_directory(script_dir)
		self._rs.sort_replies()

		# restore session
		if isinstance(ss, SessionStore):
			self._ss = ss
		else:
			raise RuntimeError("RiveBot init error: provided session store object is not a SessionStore instance.")

		self._restore_session()

		# register event callbacks
		self._rs.on('topic',    self._topic_cb)
		self._rs.on('uservar',  self._uservar_cb)

	def _topic_cb(self, user, topic, redirect=None):
		"""Topic callback.

		This is a single-user-per-rive (stateless instance) scenario; in a multi-user
		scenario within a single thread, callback functions should delegate the 
		execution to proper user session objects.
		"""
		log.debug("Topic callback: user={}, topic={}, redirect={}".format(user, topic, redirect))
		self._session.set_topic(topic, redirect)

	def _uservar_cb(self, user, name, value):
		"""Topic callback. See comment for `_topic_cb()`"""
		log.debug("User variable callback: user={}, name={}, value={}".format(user, name, value))
		self._session.set_variable(name, value)		

	def _restore_session(self):
		self._session = self._ss.load(self._user)

		# set saved user variables
		for name, value in self._session.variables():
			self._rs.set_uservar(self._user, name, value)

		# set saved topic
		topic = self._session.get_topic()
		if topic:
			if '/' in topic:
				topic, self._redirect = topic.split('/')
			self._rs.set_topic(self._user, topic)

	def _save_session(self):
		self._ss.save(self._session)

	def run(self):
		log.info("RiveBot starting...")
		if self._redirect:
			# Repeat saved redirect so that the user gets the context
			# after session restart.
			redir_reply = self._rs.redirect(self._user, self._redirect)
			print("bot> Welcome back!")
			print("bot>", redir_reply)

		while True:
		    msg = raw_input("{}> ".format(self._user))
		    if msg == '/quit':
		        self.stop()
		        break
		    reply = self._rs.reply(self._user, msg)
		    print("bot>", reply)

	def stop(self):
		log.info("RiveBot shutting down...")
		print("\nbot> Bye.")
		self._save_session()


if __name__ == "__main__":
	user  = sys.argv[1] if len(sys.argv) > 1 else 'default'
	store = SimpleSessionStore(SESSION_FILE)
	bot   = RiveBot(SCRIPT_DIR, user, store)
	try:
		bot.run()
	except (KeyboardInterrupt, EOFError):
		bot.stop()

# vim:expandtab
