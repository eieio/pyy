''' amen.py

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

from bot import MessageHandler
import re

_reAmen = re.compile('(?:will\s+)?(?:somebody|someone)\s+say\s+(.+?)(?:!|\?|\.)?$', re.I)

@MessageHandler
def _handler(context):
	m = _reAmen.match(context.message)
	if m:
		what, = m.groups()
		context.reply(what + '!')
