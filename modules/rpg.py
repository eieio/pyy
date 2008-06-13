''' rpg.py

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
from bot import BotCommandHandler, MessageHandler
import re, random, math

class Item(object):
	def __init__(self, name, stats, effects=None):
		self.name = name
		self.stats = dict()
		self.effects = dict()
		
		self.stats.update(stats or {})
		self.effects.update(effects or {})
	
	def __str__(self):
		return self.name
	
	def __repr__(self):
		return "Item('%s', %s)" % (self.name, self.buffs)
	
	def getStatsLine(self):
		return ', '.join(['%s: %d' % (key, value) for key, value in sorted(self.stats.items())])
	
	def getEffectsLine(self):
		return ', '.join(['%s: %+d' % (key, value) for key, value in sorted(self.stats.items())])

class Weapon(Item):
	def __init__(self, name, level, buffs=None):
		Item.__init__(self, name, buffs)
		self.level = level
	
	def __repr__(self):
		return "Weapon('%s', %d, %s)" % (self.name, self.level, self.buffs)

class Player(object):
	def __init__(self, name, level, stats=None):
		self.name = name
		self.level = level
		self.stats = dict()
		self.inventory = list()
		if stats:
			self.stats.update(stats)
		else:
			self.stats.update({
				'package' : 1,
				'coolness' : 1,
				'strength' : 5,
				'defense' : 5,
				'agility' : 5,
				'magic' : 0,
			})
	
	def getStats(self):
		keys = set(self.stats.keys())
		for item in self.inventory:
			keys |= set(item.buffs.keys)
		
		ret = dict.fromkeys(keys, 0)
		
		for key, value in self.stats.items():
			ret[key] += value
		
		for key in keys:
			for item in self.inventory:
				if key in item.buffs:
					ret[key] += item.buffs[key]
		
		return ret
	
	def getStatsLine(self):
		stats = self.getStats()
		return ', '.join(['%s: %d' % (key, value) for key, value in sorted(stats.items())])

def PlayerCommand(func):
	def check(context):
		player = _players.get(context.sender.nick)
		if player:
			func(context, player)
		else:
			context.reply('%s: You are not a player' % context.sender)
	check.__module__ = func.__module__
	check.__name__ = func.__name__
	check.__doc__ = func.__doc__
	return check

_players = {
	'eieio' : Player('eieio', 60, {
		'package' : 15,
		'coolness' : 10,
		'strength' : 10,
		'defense' : 10,
		'agility' : 10,
		'magic' : 10,
	}),
}

_levles = (
	'n00b',
	'scr1p7 k1dd13',
	'c0d3r',
	'h4x0r',
	'l337',
)

@BotCommandHandler('play')
def _play(context):
	if context.sender.nick not in _players:
		player = Player(context.sender.nick, 0)
		
		_players[player.name] = player
		context.reply("Created a level %d player '%s': %s" % (0, player.name, player.getStatsLine()))
	else:
		context.reply('%s is already a player' % context.sender.nick)

@BotCommandHandler('stats')
@PlayerCommand
def _stats(context, player):
	context.reply("%s's stats (lv %d): %s" % (player.name, player.level, player.getStatsLine()))
