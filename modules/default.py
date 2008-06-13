''' default.py
	Default module responsible for the basic bootstrap and protocol

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

import re
from irclib import *
import admin

_reMessage = re.compile('([^, ]+(?:,[^, ]+)*)[ ]+:(.*)')

@ProtocolHandler('NOTICE')
def do_NOTICE(context):
	if not context.isConnected():
		context.proc.nick(context.getNick())
		context.proc.user(context.getNick(), context.getHost())
		
		context.setConnected(True)

@ProtocolHandler('376')
def do_376(context):
	for channel in context.getTargetChannels():
		context.proc.join(channel)
	if context.getSetting('password'):
			context.proc.privmsg('nickserv', 'IDENTIFY %s' % context.getSetting('password'))

@ProtocolHandler('PING')
def do_PING(context):
	context.proc.pong(context.params)

@ProtocolHandler('ERROR')
def do_ERROR(context):
	context.proc.exit()
