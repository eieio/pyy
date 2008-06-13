''' basic.py
	Basic module

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
from bot import BotCommandHandler
import re, sys

@BotCommandHandler('modules')
@trusted
def _modules(context):
	'''Lists the loaded modules'''
	context.reply('Modules loaded: %s' % ', '.join(sorted(context.proc.modules.keys())))

@BotCommandHandler('load')
@trusted('admin')
def _load(context):
	'''Usage: load <module name>\nAttempts to load the named module'''
	module = (context.args or '').strip()
	try:
		if module not in context.proc.modules:
			context.proc.loadModule(module)
			context.reply("Loaded module '%s' successfully" % module)
		else:
			context.reply("Module '%s' already loaded" % module)
	except:
		context.reply("Error loading module '%s': %s" % (module, str(sys.exc_value)))

@BotCommandHandler('do')
@trusted
def _do(context):
	'''Usage: do [@(nick | channel)] <message>\nDirects the given message at nick or channel as a CTCP action'''
	m = re.match('(?:@(#{0,2}[^\s]+)\s+)?(.*)', context.args)
	if m:
		where, what = m.groups()
		
		if where:
			context.proc.action(where, what)
		else:
			context.proc.action(context.replyto(), what)
	else:
		context.reply("I do not understand '%s'" % context.args)

@BotCommandHandler('say')
@trusted
def _say(context):
	'''Usage: do [@(nick | channel)] <message>\nDirects the given message at nick or channel'''
	m = re.match('(?:@(#{0,2}[^\s]+)\s+)?(.*)', context.args)
	if m:
		where, what = m.groups()
		
		if where:
			context.proc.privmsg(where, what)
		else:
			context.proc.privmsg(context.replyto(), what)
	else:
		context.reply("I do not understand '%s'" % context.args)

@BotCommandHandler('server')
@trusted('admin')
def _server(context):
	'''Usage: server <IRC protocol string>\nSends the given raw protocol string to the server'''
	context.proc._socket.sendall(context.args + '\r\n')
