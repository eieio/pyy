''' http.py

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

from bot import MessageHandler, BotCommandHandler
from admin import trusted
import re, urllib

_reURL = re.compile('.*?((?:(https?)://|(?=www\.))[\w:#@%/;$()~_?\+-=\\\.&]+).*?')
_reTitle = re.compile('<title>(.*?)</title>', re.I | re.M)

_enabled = True

@BotCommandHandler('http')
@trusted
def _http(context):
	'''Usage: http [enable|disable]\nEnables or disables URL titles; no param returns state'''
	m = re.match('\s*(enable|disable)\s*', context.args or '', re.I)
	if m:
		op, = m.groups()
		
		global _enabled
		
		_enabled = op.lower() == 'enable'
	elif not (context.args or ''):
		context.reply('http titles %s' % ['DISABLED', 'ENABLED'][_enabled])
	else:
		context.reply('Usage: http [enable|disable]')

@MessageHandler
def _handler(context):
	m = _reURL.match(context.message)
	if _enabled and m:
		address, proto = m.groups()
		
		if not proto:
			address = 'http://' + address
		
		if proto in ('http', 'https', None):
			fin = urllib.urlopen(address)
			if fin.headers.gettype() == 'text/html':
				title = ' '.join(_reTitle.findall(fin.read(4096))).strip()
				fin.close()
				if title:
					context.reply('Title: ' + title)
