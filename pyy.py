''' IRCBot.py
	
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

import sys
import socket
import random
from irclib import *

# TODO: move this to a config file at some point

HOST = 'irc.freenode.net'
PORT = 6667
NICK = 'pyy_%04x' % random.getrandbits(16)	# bot nick, change it
PASS = ''									# password used to identify to services
MASTER = ''									# default admin nick, set it to your own nick
CHANNELS = ('#pyy', )						# channels to join at startup
	
if __name__ == '__main__':
	logfile = file('logfile.txt', 'wb')
	
	so = socket.socket()
	so.connect((HOST, PORT))
	
	bot = CommandProcessor(so, NICK, HOST, CHANNELS, logfile,
		password=PASS, autorejoin=True, master=MASTER)
	
	bot.cmdloop()
