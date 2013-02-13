''' threaded.py
	Threaded command module

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

import threading

def threaded(func):
	def delegate(context):
		t = threading.Thread(target=func, args=(context,));
		t.start();
	
	delegate.__module__ = func.__module__
	delegate.__name__ = func.__name__
	delegate.__doc__ = func.__doc__

	return delegate

