''' ctcp.py
	CTCP support module

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

from bot import MessageContext, MessageHandler
from admin import trusted
import re, sys

_reMessage = re.compile('([^, ]+(?:,[^, ]+)*)[ ]+:(.*)')
_reCtcpCommand = re.compile('\x01([A-Z]+)\s*(.*)\x01')
_ctcpCommandHandlers = dict()

class CtcpCommandContext(MessageContext):
	def __init__(self, context, command, args):
		MessageContext.__init__(self, context, context.receivers, context.message)
		self.command = command
		self.args = args
	
	def __str__(self):
		return 'Command: %s %s %s %s' % (self.sender, self.receivers, self.command, self.args)

def CtcpCommandHandler(arg):
	if isinstance(arg, str):
		def execute(func):
			registerCtcpCommand(func, arg)
			return func
		return execute
	else:
		registerCtcpCommand(func, func.__name__)
		return func

def registerCtcpCommand(handler, name):
	name = name.upper()
	if name in _ctcpCommandHandlers:
		_ctcpCommandHandlers[name].append(handler)
	else:
		_ctcpCommandHandlers[name] = [handler]
	
	print "Registered CTCP command '%s'" % name

@MessageHandler
def _handler(context):
	m = _reCtcpCommand.match(context.message)
	if m:
		command, args = m.groups()
		
		for handler in _ctcpCommandHandlers.get(command.upper(), []):
			try:
				handler(CtcpCommandContext(context, command, args))
			except:
				context.log('!!!', str(sys.exc_value))

@CtcpCommandHandler('VERSION')
def _VERSION(context):
	if not context.args:
		context.proc.notice(context.sender, '\x01VERSION %s:%s:%s\x01'  % ('pyy', '0.1a', 'Awesome'))

@CtcpCommandHandler('FINGER')
def _FINGER(context):
	if not context.args:
		context.proc.notice(context.sender, "\x01FINGER :Don't give me the finger, dude! :I don't appreciate it!\x01")