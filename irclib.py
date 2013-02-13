''' irclib.py
	
   Copyright 2008 Corey Tabaka

   Licensed under the Apache License, Version 2.0 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.
'''

import sys
import os
import socket
import string
import re
import traceback

class IRCProtocol(object):
	def __init__(self, socket, logfile=None):
		self._socket = socket
		self._logfile = logfile
	
	def log(self, msg, *args):
		if not self._logfile: return
		
		if args:
			msg += ' ' + ' '.join(args)
		if msg.endswith('\r\n'):
			self._logfile.write(msg)
			print msg,
		else:
			self._logfile.write('%s\r\n' % msg)
			print msg
		self._logfile.flush()
	
	def nick(self, nickname):
		self.log('<<<', 'NICK %s\r\n' % nickname)
		self._socket.sendall('NICK %s\r\n' % nickname)
	
	def user(self, username, hostname, servername='servername', realname='Python'):
		self.log('<<<', 'USER %s %s %s :%s\r\n' % (username, hostname, servername, realname))
		self._socket.sendall('USER %s %s %s :%s\r\n' % (username, hostname, servername, realname))
	
	def quit(self, message='Client quitting'):
		self.log('<<<', 'QUIT :%s\r\n' % message.strip('\n'))
		self._socket.sendall('QUIT :%s\r\n' % message.strip('\n'))
	
	def join(self, *args, **kv):
		if args:
			self.log('<<<', 'JOIN %s\r\n' % ','.join(args))
			self._socket.sendall('JOIN %s\r\n' % ','.join(args))
		elif kv:
			self.log('<<<', 'JOIN %s %s\r\n' % (','.join(kv.keys()), ','.join(kv.values())))
			self._socket.sendall('JOIN %s %s\r\n' % (','.join(kv.keys()), ','.join(kv.values())))
	
	def part(self, *channels):
		self.log('<<<', 'PART %s\r\n' % ','.join(channels))
		self._socket.sendall('PART %s\r\n' % ','.join(channels))
	
	def ping(self, *servers):
		self.log('<<<', 'PING %s\r\n' % ' '.join(servers[:2]))
		self._socket.sendall('PING %s\r\n' % ' '.join(servers[:2]))
	
	def pong(self, *servers):
		self.log('<<<', 'PONG %s\r\n' % ' '.join(servers[:2]))
		self._socket.sendall('PONG %s\r\n' % ' '.join(servers[:2]))
	
	def privmsg(self, target, message):
		self.log('<<<', 'PRIVMSG %s :%s\r\n' % (target, message.strip('\r\n')))
		self._socket.sendall('PRIVMSG %s :%s\r\n' % (target, message.strip('\r\n')))
	
	def notice(self, target, message):
		self.log('<<<', 'NOTICE %s :%s\r\n' % (target, message.strip('\r\n')))
		self._socket.sendall('NOTICE %s :%s\r\n' % (target, message.strip('\r\n')))
	
	def mode(self, name, flags, *args):
		self.log('<<<', 'MODE %s %s %s\r\n' % (name, flags, ' '.join(args)))
		self._socket.sendall('MODE %s %s %s\r\n' % (name, flags, ' '.join(args)))
	
	def whois(self, nick):
		self.log('<<<', 'WHOIS %s\r\n' % nick)
		self._socket.sendall('WHOIS %s\r\n' % nick)
	
	def action(self, target, message):
		self.log('<<<', 'PRIVMSG %s :\x01ACTION %s\x01\r\n' % (target, message))
		self._socket.sendall('PRIVMSG %s :\x01ACTION %s\x01\r\n' % (target, message))

def isnull(value, default):
	if value != None:
		return value
	else:
		return default

class Sender:
	def __init__(self, nick, type, user, host):
		self.nick = nick
		self.type = type
		self.user = user
		self.host = host
	def __str__(self):
		return self.nick
	def __repr__(self):
		return "'%s'" % self.nick

class ProtocolContext(object):
	def __init__(self, proc, sender, id, params):
		self.proc = proc
		self.sender = sender
		self.id = id
		self.params = params
	
	def __str__(self):
		return 'Protocol: %s %s %s' % (self.sender, self.id, self.params)
	
	def isConnected(self):
		return self.proc._connected
	
	def setConnected(self, value):
		self.proc._connected = bool(value)
	
	def getNick(self):
		return self.proc._nick
	
	def getHost(self):
		return self.proc._host
	
	def getTargetChannels(self):
		return self.proc._targetChannels
	
	def getSetting(self, name):
		return self.proc._settings.get(name)
	
	def log(self, *args):
		self.proc.log(*args)

def _import(name):
	mod = __import__(name)
	components = name.split('.')
	for comp in components[1:]:
		mod = getattr(mod, comp)
	return mod

def ProtocolHandler(arg):
	if isinstance(arg, str):
		def execute(func):
			CommandProcessor.registerHandler(func, arg)
			return func
		return execute
	else:
		CommandProcessor.registerHandler(func, func.__name__)
		return func

class CommandProcessor(IRCProtocol):
	reCommand = re.compile('(?::([^ ]+)[ ]+)?([a-zA-Z]+|\d\d\d)[ ]*(.*)')
	reSender = re.compile('([^!@ ]+)(?:!(?:([in])=)?([^@ ]+))?(?:@([^ ]+))?')
	
	modules = dict()
	handlers = dict()
	
	_exit = False
	
	@staticmethod
	def registerHandler(handler, name):
		name = name.upper()
		if name in CommandProcessor.handlers:
			CommandProcessor.handlers[name].append(handler)
		else:
			CommandProcessor.handlers[name] = [handler]
		
		print 'Registered handler', name
		
	def __init__(self, socket, nick, host, channels, logfile=None, **kv):
		IRCProtocol.__init__(self, socket, logfile)
		self._connected = False
		self._nick = nick
		self._host = host
		
		if isinstance(channels, str):
			self._targetChannels = set([channels])
		else:
			self._targetChannels = set(channels)
		
		self._settings = dict()
		self._settings.update(kv)
		self.__quit = False
		
		if not self.modules:
			home = os.getcwd()
			path = os.path.join(home, 'modules')
			modules = [os.path.splitext(p)[0] for p in os.listdir(path) if p.endswith('.py') and p != '__init__.py']
			
			for name in modules:
				try:
					self.loadModule(name)
				except:
					self.log('!!!', traceback.format_exc())
	
	def loadModule(self, name):
		module = _import('modules.%s' % name)
		self.modules[name] = module
	
	def close(self):
		self.__quit = True
	
	def exit(self):
		CommandProcessor._exit = True
	
	def evaluate(self, msg):
		if msg.startswith('ERROR :Closing Link'):
			self.log('!!!', msg)
			self.close()
			return
		
		m = self.reCommand.match(msg)
		if not m: 
			self.log('!!!', 'Malformed message from server: %s' % msg)
			return
		
		prefix, id, params = m.groups()
		m = self.reSender.match(prefix or '')
		
		if m:
			sender = Sender(*m.groups())
		else:
			sender = Sender('', '', '', '')
		
		for handler in self.handlers.get(id.upper(), []):
			try:
				handler(ProtocolContext(self, sender, id, params))
			except:
				self.log('!!!', str(sys.exc_value))
			
			if self.__quit:
				break
	
	def cmdloop(self):
		newline = re.compile('\r\n')
		buffer = ''

		self.nick(self._nick)
		self.user(os.getlogin(), socket.gethostname(), self._host, 'pyy')
		
		while not (self.__quit or CommandProcessor._exit):
			buffer += self._socket.recv(1)
			
			if '\r\n' in buffer:
				msg, buffer = newline.split(buffer, 1)
				self.log('>>>', msg)
				
				self.evaluate(msg)
