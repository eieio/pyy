''' admin.py
	Administration module

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

# put this here to handle circular import from bot and other modules
def trusted(*args):
	if len(args) > 1 or isinstance(args[0], str):
		def delegate(func):
			def check(context):
				admin = _administrators.get(context.sender.nick) or _aliases.get(context.sender.nick)
				if admin and admin.trusted(context.sender):
					if admin.checkAccess(*args):
						func(context)
					else:
						context.reply("%s: I don't trust you that much" % context.sender)
				else:
					context.reply('%s: You are not trusted' % context.sender)
			check.__module__ = func.__module__
			check.__name__ = func.__name__
			check.__doc__ = func.__doc__
			return check
		
		return delegate
	else:
		func = args[0]
		def check(context):
			admin = _administrators.get(context.sender.nick) or _aliases.get(context.sender.nick)
			if admin and admin.trusted(context.sender):
				func(context)
			else:
				context.reply('%s: You are not trusted' % context.sender)
		check.__module__ = func.__module__
		check.__name__ = func.__name__
		check.__doc__ = func.__doc__
		return check

def isAdmin(context):
	admin = _administrators.get(context.sender.nick) or _aliases.get(context.sender.nick)
	return bool(admin and admin.trusted(context.sender))

from irclib import ProtocolHandler
from bot import BotCommandHandler
import channel
import re, anydbm, sys, atexit

_reNick = re.compile('^[a-zA-Z_][\w_\-\[\]\\`^{}]*$')
_reTrust = re.compile('\s*([a-zA-Z_][\w_\-\[\]\\`^{}]*)(?:\s+([^\s,]+(?:[\s,]+[^\s,]+)*))?')
_reAccessList = re.compile('\s*list\s+([^\s]+)')
_reAccessAdd = re.compile('\s*add\s+([^\s]+)\s+([^\s,]+(?:[\s,]+[^\s,]+)*)')
_reAccessRemove = re.compile('\s*remove\s+([^\s]+)\s+([^\s,]+(?:[\s,]+[^\s,]+)*)')
_reAccessArgs = re.compile('[\s,]+')

def _filterNick(nick):
	nick = (nick or '').strip()
	m = _reNick.match(nick)
	if m:
		return nick
	else:
		return ''

class AdminUser(object):
	def __init__(self, nick, access=''):
		self.nick = nick
		self.user = ''
		self.host = ''
		self.identified = False
		self.alias = ''
		self.events = dict()
		if isinstance(access, (str, type(None))):
			self.access = set(_reAccessArgs.split(access or ''))
		else:
			self.access = set(access)
	
	def trusted(self, sender):
		return self.identified and sender.user == self.user and sender.host == self.host
	
	def checkAccess(self, *flags):
		return set(flags).issubset(self.access)
	
	def addAccess(self, *flags):
		flags = set(flags)
		flags -= set([''])
		self.access |= flags
		
		self.dbAdd()
	
	def removeAccess(self, *flags):
		self.access -= set(flags)
		
		self.dbAdd()
	
	def invalidate(self):
		self.host = ''
		self.user = ''
		self.identified = False
	
	def runEvent(self, name):
		response = self.events.get(name)
		if response:
			del self.events[name]
			response()
	
	def setEvent(self, name, handler):
		self.events[name] = handler
	
	def dbRemove(self):
		del _db[self.nick]
		_db.sync()
	
	def dbAdd(self):
		_db[self.nick] = ','.join(self.access)
		_db.sync()

# load/create the admin db
_db = anydbm.open('administrators.db', 'c')
atexit.register(_db.close)

# create a default user using the master nick in pyy
if not len(_db):
	import pyy
	try:
		_db[pyy.MASTER] = 'admin'
	except:
		print 'Failed to create default admin user:', str(sys.exc_value)

_administrators = dict([(nick, AdminUser(nick, access)) for nick, access in _db.iteritems()])
_aliases = dict()

@BotCommandHandler('auth')
def _auth(context):
	'''Usage: auth\nRequests the bot to verify the sender's admin status'''
	admin = _administrators.get(context.sender.nick) or _aliases.get(context.sender.nick)
	if admin:
		if admin.identified:
			context.reply('%s is already trusted' % context.sender.nick)
		else:
			context.reply('Checking services...')
			
			def event():
				context.reply('%s is identified by services' % context.sender.nick)	
			admin.setEvent('auth_whois', event)
			
			context.proc.whois(context.sender.nick)
	else:
		context.reply('%s is not an admin' % context.sender.nick)

@BotCommandHandler('trust')
@trusted
def _trust(context):
	'''Usage: trust <nick> [flag [, flag]...]\nAdds nick to the list of admins with the specified access flags'''
	m = _reTrust.match(context.args)
	if m:
		nick, access = m.groups()
		
		if nick in _aliases:
			context.reply('%s (%s) is already trusted; use access to modify' % (nick, _aliases[nick].nick))
		elif nick in _administrators:
			context.reply('%s is already trusted; use access to modify' % nick)
		else:
			if access:
				admin = _administrators.get(context.sender.nick) or _aliases.get(context.sender.nick)
				if admin.checkAccess('admin'):
					user = AdminUser(nick, access)
					_administrators[nick] = user
					user.dbAdd()
					
					context.reply('%s is now trusted with access: %s' % (nick, ','.join(sorted(user.access))))
					context.proc.whois(nick)
				else:
					context.reply("%s: you don't have the right to grant access" % context.sender.nick)
			else:
				user = AdminUser(nick)
				_administrators[nick] = user
				user.dbAdd()
				
				context.reply('%s is now trusted' % nick)
				context.proc.whois(nick)
	else:
		context.reply('Usage: trust <nick>')

@BotCommandHandler('untrust')
@trusted
def _untrust(context):
	'''Usage: untrust <nick>\nRemoves nick from the list of admins'''
	nick = _filterNick(context.args)
	if nick:
		admin = _administrators.get(nick) or _aliases.get(nick)
		if admin:
			if admin.nick == context.getSetting('master'):
				context.reply('%s: Nigga, please!' % context.sender.nick)
			else:
				del _administrators[admin.nick]
				admin.dbRemove()
				
				if nick in _aliases:
					del _aliases[nick]
				
				if nick == admin.nick:
					context.reply('%s is no longer trusted' % nick)
				else:
					context.reply('%s (%s) is no longer trusted' % (nick, admin.nick))
		else:
			context.reply('%s is already not trusted' % nick)
	else:
		context.reply('Usage: untrust <nick>')

@BotCommandHandler('access')
@trusted('admin')
def _access(context):
	'''Usage: access <list|add|remove> <nick> [flag [, flag]...]\nLists, adds, or removes access flags from nick'''
	m = _reAccessList.match(context.args)
	if m:
		nick, = m.groups()
		admin = _administrators.get(nick) or _aliases.get(nick)
		
		if admin:
			context.reply('%s has access: %s' % (nick, ', '.join(sorted(admin.access))))
		else:
			context.reply('%s is not trusted' % nick)
		
		return
	
	m = _reAccessAdd.match(context.args)
	if m:
		nick, access = m.groups()
		admin = _administrators.get(nick) or _aliases.get(nick)
		
		if admin:
			access = _reAccessArgs.split(access)
			admin.addAccess(*access)
		else:
			context.reply('%s is not trusted' % nick)
		
		return
	
	m = _reAccessRemove.match(context.args)
	if m:
		nick, access = m.groups()
		admin = _administrators.get(nick) or _aliases.get(nick)
		
		if admin:
			access = _reAccessArgs.split(access)
			admin.removeAccess(*access)
		else:
			context.reply('%s is not trusted' % nick)
		
		return
	
	context.reply('Usage: access <list|add|remove> <nick> [name [, name]...]')

@ProtocolHandler('NICK')
def _nick(context):
	nick = context.params.lstrip(':')
	admin = _administrators.get(context.sender.nick) or _aliases.get(context.sender.nick)
	
	if admin:
		if admin.alias:
			del _aliases[admin.alias]
		
		if nick not in _administrators:
			_aliases[nick] = admin
			admin.alias = nick
		elif admin != _administrators[nick]:
			admin.alias = ''
			_administrators[nick].invalidate()
			context.proc.whois(nick)
		else:
			admin.alias = ''

@ProtocolHandler('JOIN')
def _join(context):
	admin = _administrators.get(context.sender.nick)
	if admin:
		context.proc.whois(context.sender.nick)

@ProtocolHandler('PART')
def _part(context):
	admin = _administrators.get(context.sender.nick) or _aliases.get(context.sender.nick)
	if admin:
		channels = channel.getChannelsForNick(context.sender.nick)
		
		if not channels and context.sender.nick in _aliases:
			del _aliases[context.sender.nick]

@ProtocolHandler('311')
def _311(context):
	m = re.match('([^\s]+)\s+([^\s]+)\s+(?:([in])=)?([^@ ]+)\s+([^\s]+)\s*(.*)', context.params)
	if m:
		me, nick, in_, user, host, other = m.groups()
		admin = _administrators.get(nick)
		if admin:
			admin.user = user
			admin.host = host

@ProtocolHandler('320')
def _320(context):
	m = re.match('([^\s]+)\s+([^\s]+)\s+:(.*)', context.params)
	if m:
		me, nick, message = m.groups()
		admin = _administrators.get(nick)
		
		if admin and 'is identified to services' in message:
			admin.identified = True
			admin.runEvent('auth_whois')
