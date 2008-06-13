''' bot.py
	Bot command processing facilities

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

from irclib import *
from admin import trusted
import re, sys
import pyy

# TODO: rebuild bot command pattern on bot nick change

def makeBotCommandPattern(nick):
	return re.compile('(?:%s[,:]?\s+!?|!)((?:\w+\.)*)([^\s]+)\s*(.*)' % re.escape(nick))

_reMessage = re.compile('([^, ]+(?:,[^, ]+)*)[ ]+:(.*)')
_reModuleName = re.compile('^(?:modules.)?(.*)$')
#_reBotCommand = re.compile('(?:py[,:]?\s+!?|!)((?:\w+\.)*)([^\s]+)\s*(.*)')
try:
	_reBotCommand = makeBotCommandPattern(pyy.NICK)
except:
	print '!!! Failed to create bot command pattern:', str(sys.exc_value)
	_reBotCommand = re.compile('!((?:\w+\.)*)([^\s]+)\s*(.*)')

_botCommandHandlers = dict()
_messageHandlers = list()

def _moduleName(s):
	m = _reModuleName.match(s)
	if m:
		return m.groups()[0]
	else:
		return ''

class BotCommandContext(ProtocolContext):
	def __init__(self, context, receivers, command, args):
		ProtocolContext.__init__(self, context.proc, context.sender, context.id, context.params)
		self.receivers = receivers
		self.command = command
		self.args = args
	
	def __str__(self):
		return 'Command: %s %s %s %s' % (self.sender, self.receivers, self.command, self.args)
	
	def replyto(self):
		if self.proc._nick == self.receivers:
			return self.sender.nick
		else:
			return self.receivers
	
	def reply(self, msg):
		self.proc.privmsg(self.replyto(), msg)

class MessageContext(ProtocolContext):
	def __init__(self, context, receivers, message):
		ProtocolContext.__init__(self, context.proc, context.sender, context.id, context.params)
		self.receivers = receivers
		self.message = message
	
	def __str__(self):
		return 'Message: %s %s %s' % (self.sender, self.receivers, self.message)
	
	def replyto(self):
		if self.proc._nick == self.receivers:
			return self.sender.nick
		else:
			return self.receivers
	
	def reply(self, msg):
		self.proc.privmsg(self.replyto(), msg)

def BotCommandHandler(arg):
	if isinstance(arg, str):
		def execute(func):
			registerBotCommand(func, arg)
			return func
		return execute
	else:
		registerBotCommand(func, func.__name__)
		return func

def MessageHandler(func):
	registerMessageHandler(func)
	return func

def registerBotCommand(handler, name):
	name = name.lower()
	if name in _botCommandHandlers:
		_botCommandHandlers[name].append(handler)
	else:
		_botCommandHandlers[name] = [handler]
	
	module = _moduleName(handler.__module__)
	
	print "Registered bot command '%s' from module '%s'" % (name, module)

def registerMessageHandler(handler):
	if handler not in _messageHandlers:
		_messageHandlers.append(handler)
	
	print "Registered message handler '%s' from module '%s'" % (handler.__name__, _moduleName(handler.__module__))

@ProtocolHandler('PRIVMSG')
def _handler(context):
	m = _reMessage.match(context.params)
	if m:
		receivers, message = m.groups()
		
		m = _reBotCommand.match(message)
		if m:
			module, command, args = m.groups()
			qualifiedCommand = (module or '') + command
			
			context = BotCommandContext(context, receivers, command, args)
			
			handlers = _botCommandHandlers.get(command.lower(), [])
			if len(handlers) == 1:
				try:
					handlers[0](context)
				except:
					context.log('!!!', str(sys.exc_value))
			elif len(handlers) > 1:
				if module:
					commands = [handler for handler in handlers if module.lower() == _moduleName(handler.__module__).lower()]
					if len(commands) == 1:
						try:
							commands[0](context)
						except:
							context.log('!!!', str(sys.exc_value))
					elif len(commands) > 1:
						context.reply("Multiple commands with the same name defined in module '%s'" \
							% module)
					else:
						#context.reply("Unknown command '%s'" % qualifiedCommand)
						pass
				else:
					options = ['%s.%s' % (_moduleName(handler.__module__), command) for handler in handlers]
					context.reply("Ambiguous command '%s'; possible options: %s" \
						% (command, ', '.join(options)))
			else:
				#context.reply("Unknown command '%s'" % qualifiedCommand)
				pass
		else:
			for handler in _messageHandlers:
				try:
					handler(MessageContext(context, receivers, message))
				except:
					context.log('!!!', str(sys.exc_value))

@BotCommandHandler('commands')
def _commands(context):
	'''Usage: commands\nLists the available bot commands'''
	context.reply('Commands: %s' % ', '.join(sorted(_botCommandHandlers.keys())))

@BotCommandHandler('help')
def _help(context):
	'''Usage: help <command name>\nUse !commands for a list of commands'''
	command = (context.args or '').strip()
	handlers = _botCommandHandlers.get(command, [])
	if handlers:
		for handler in handlers:
			if handler.__doc__:
				for line in re.split('\r?\n', handler.__doc__):
					context.reply('[%s.]%s: %s' % (_moduleName(handler.__module__), command, line))
			else:
				context.reply('[%s.]%s: No help available' % (_moduleName(handler.__module__), command))
	else:
		if command:
			context.reply("unknown command '%s'" % command)
		else:
			context.reply('Usage: help <command name>; Use !commands for a list of commands')

@BotCommandHandler('quit')
@trusted('admin')
def _quit(context):
	'''Usage: quit [message]\nExits the bot, optionally with the given reason'''
	import time
	context.proc.quit(context.args or 'Received SIGSIGNOFF')
	time.sleep(2)
	context.proc.exit()
