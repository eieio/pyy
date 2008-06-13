''' channel.py

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
from bot import BotCommandHandler
from admin import trusted
import admin
import re

_re353 = re.compile('([^\s]+)\s+=\s+(#{0,2}[^\s]+)\s+:(.*)')
_reKick = re.compile('(#{0,2}[^\s]+)\s+([^\s]+)(?:\s+:(.*))?')

_currentChannels = dict()

def getChannelsForNick(nick):
	return [channel for channel in _currentChannels.values() if nick in channel.members]

class Channel(object):
	def __init__(self, name):
		self.name = name
		self.members = set()
	
	def __hash__(self):
		return hash(self.name)
	
	def __str__(self):
		return self.name
	
	def addMembers(self, *nicks):
		nicks = [nick.strip('@&') for nick in nicks]
		self.members |= set(nicks)
	
	def removeMembers(self, *nicks):
		nicks = [nick.strip('@&') for nick in nicks]
		self.members -= set(nicks)
	
@BotCommandHandler('channels')
@trusted
def _channels(context):
	'''Usage: channels\nLists the channels that the bot is in'''
	context.reply('channels: %s' % ', '.join(sorted(_currentChannels.keys())))

@BotCommandHandler('join')
@trusted('admin')
def _join(context):
	'''Usage: join channel [, channel]...\nDirects the bot to join the given channels'''
	channels = set(re.split('[\s,]+', context.args or ''))
	channels -= set([''])
	channels -= set(_currentChannels.keys())
	
	for channel in channels:
		context.proc.join(channel)

@BotCommandHandler('part')
@trusted('admin')
def _part(context):
	'''Usage: join channel [, channel]...\nDirects the bot to leave the given channels'''
	channels = set(re.split('[\s,]+', context.args or ''))
	channels &= set(_currentChannels.keys())
	
	for channel in channels:
		del _currentChannels[channel]
		context.proc.part(channel)

@ProtocolHandler('JOIN')
def _JOIN(context):
	channel = (context.params or '').strip(': ')
	
	if channel:
		if context.sender.nick == context.getNick():
			_currentChannels[channel] = Channel(channel)
		elif channel in _currentChannels:
			_currentChannels[channel].addMembers(context.sender.nick)

@ProtocolHandler('353')
def _353(context):
	m = _re353.match(context.params or '')
	if m:
		me, chan, nicks = m.groups()
		
		if me == context.getNick() and chan in _currentChannels:
			_currentChannels[chan].addMembers(*re.split('\s+', nicks.strip()))

@ProtocolHandler('KICK')
def _KICK(context):
	m = _reKick.match(context.params)
	if m:
		chan, me, message = m.groups()
		
		if context.getSetting('autorejoin'):
			context.proc.join(chan)
			
			if admin.isAdmin(context):
				context.proc.action(chan, 'licks %s' % context.sender.nick)
			else:
				context.proc.action(chan, 'glares at %s' % context.sender.nick)
		else:
			del _currentChannels[chan]

@ProtocolHandler('PART')
def _PART(context):
	channel = (context.params or '').strip(': ')
	
	if channel in _currentChannels:
		_currentChannels[channel].removeMembers(context.sender.nick)

@ProtocolHandler('QUIT')
def _QUIT(context):
	for channel in _currentChannels.values():
		channel.removeMembers(context.sender.nick)

@ProtocolHandler('NICK')
def _NICK(context):
	nick = context.params.lstrip(':')
	
	for channel in _currentChannels.values():
		channel.removeMembers(context.sender.nick)
		channel.addMembers(nick)
