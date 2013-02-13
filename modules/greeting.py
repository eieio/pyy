''' greeting.py
	Greetings and content response module

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

from irclib import ProtocolContext, ProtocolHandler
from bot import MessageHandler, BotCommandHandler
from admin import trusted
import basic
import re
import random
import pyy

_reMessage = re.compile('([^, ]+(?:,[^, ]+)*)[ ]+:(.*)')
_rePart = re.compile('([^\s]+)\s*(?::(.*))?')

_greetings = {
	getattr(pyy, 'MASTER', '') : {
		'JOIN' : ["I'm ready master"],
		'PART' : ['*snif*', '\x01ACTION cries\x01', '*bark*'] + [None] * 5,
		'QUIT' : ['*snif*', '\x01ACTION cries\x01', '*bark*'] + [None] * 5,
		'PRIVMSG' : ["Ain't it the truth?"] + [None] * 8,
	},
}

_default = {
	'JOIN' : ['hi %s', '\x01ACTION looks %s up and down\x01'] + [None] * 3,
	'PART' : ['see ya', 'see ya %s'] + [None] * 4,
	'QUIT' : ['see ya', 'see ya %s'] + [None] * 4,
}

SILENT = 0
KNOWN = 1
ALL = 2

_mode = SILENT
_modeNames = ['SILENT', 'KNOWN', 'ALL']

def _doGreeting(context, channel):
	if _mode == ALL:
		target = _greetings.get(context.sender.nick) or _default
	elif _mode == KNOWN:
		target = _greetings.get(context.sender.nick)
	else:
		target = None
	
	if target and channel and context.sender.nick != context.getNick():
		action = random.choice(target.get(context.id, [None]) + _default.get(context.id, []))
		if action:
			if '%s' in action:
				context.proc.privmsg(channel, action % context.sender.nick)
			else:
				context.proc.privmsg(channel, action)

@BotCommandHandler('greet')
@trusted
def _greet(context):
	'''Usage: greet [silent|known|all]\nSets the current greeting mode or returns the mode when no param is specified'''
	op = (context.args or '').strip().lower()
	
	global _mode
	
	if op == 'silent':
		_mode = SILENT
	elif op == 'known':
		_mode = KNOWN
	elif op == 'all':
		_mode = ALL
	elif op == '':
		pass
	else:
		context.reply('Usage: greet [silent|known|all]')
		return
	
	context.reply('greeting mode is %s' % (_modeNames[_mode]))

@ProtocolHandler('JOIN')
def _JOIN(context):
	channel = (context.params or '').strip(': ')
	_doGreeting(context, channel)

@ProtocolHandler('QUIT')
def _QUIT(context):
	channel = (context.params or '').strip(': ')
	_doGreeting(context, channel)

@MessageHandler
def _PRIVMSG(context):
	m = _reMessage.match(context.params)
	if m:
		receivers, message = m.groups()
		_doGreeting(context, receivers)

@ProtocolHandler('PART')
def _PART(context):
	m = _rePart.match(context.params or '')
	if m:
		channel, message = m.groups()
		_doGreeting(context, channel)

@ProtocolHandler('NOTICE')
def _NOTICE(context):
	m = _reMessage.match(context.params)
	if m:
		receivers, message = m.groups()
		_doGreeting(context, receivers)
