#!/usr/bin/env python
#
# rat rlist - Router Automation Toolkit: router lister
# (C) 2013 Tomas Hlavacek (tmshlvck@gmail.com)
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


"""
This module reads and filters list of routers (or any other network devices).
"""

# Global helpers and constants
DEVICE_LIST = "~/.rat-device-list"
""" Path to the text list of devices. Usually /etc/rat/device-list.txt . """

# End of helpers and constants

import os


class ParseError(Exception):
	""" rlist parse exception class """
	def __init__(self,message,line):
		Exception.__init__(self,message+" on line: "+line)


class HostSpec(object):
	def __init__(self, line=None, defaults=None):
		self.shortname = None
		self.hostname = None
		self.type = None
		self.enabled = False
		self.user = None
		self.password = None
		self.enablepassword = None
		self.port = None
		
		if line:
			self.parseLine(line, defaults)

	def init(self, hostname, host_type, enabled=False, user=None, password=None, enablepassword=None, port=None, shortname=None):
		""" Set contents of the object based on externally-fed arguments. """
		if not hostname:
			raise Exception("Can not init HostSpec object without name.")
		if not host_type:
			raise Exception("Can not init HostSpec object without host type.")

		self.shortname = hostname.split('.',1)[0] if not shortname else shortname
		self.hostname = hostname
		self.type = host_type
		self.enabled = enabled
		self.user = user
		self.password = password
		self.enablepassword = enablepassword
		self.port = port

	def clone(self):
		""" Create and return a new object with the same internal contents. """
		hc = HostSpec()
		hc.init(self.hostname, self.type, self.enabled, self.user, self.password, self.enablepassword, self.port, self.shortname)
		return hc

	def parseLine(self, line, defaults=None):
		""" Read object contents from device-list file.  """

		def parseHostnameGroup(group):
			s = group.split(":",1)
			if len(s) == 1:
				return (group,None)
			else:
				return (s[0],int(s[1]))
			
		g = line.lstrip().split()
		l = len(g)
		if l > 7:
			raise ParseError("Too much groups on line.", line, l)


		if l < 4:
			raise ParseError("Too few groups on line.", line, l)

		self.shortname = g[0]
		(self.hostname, self.port) = parseHostnameGroup(g[1])
		self.type = g[2]
		self.enabled = int(g[3])
		if l >= 5:
			self.user = g[4]
		else:
			if self.type in defaults and not self.isDefault():
				self.user = defaults[self.type].user
		if l >= 6:
			self.password = g[5]
		else:
			if self.type in defaults and not self.isDefault():
				self.password = defaults[self.type].password
		if l == 7:
			self.enablepassword = g[6]
		else:
			if self.type in defaults and not self.isDefault():
				self.enablepassword = defaults[self.type].enablepassword

	def getList(self,  anonymize=False):
		def anon(string, anonymize):
			if not string:
				return string
			
			if anonymize:
				return '*'*len(string)
			else:
				return string

		def joinPort(hostname,port):
			if port:
				return hostname+":"+str(port)
			else:
				return hostname
		
		return [self.shortname,
			joinPort(self.hostname, self.port),
			self.type,
			str(self.enabled),
			self.user,
			anon(self.password,  anonymize),
			anon(self.enablepassword, anonymize)]


	def getLine(self, anonymize=False):
		return '\t'.join([e for e in self.getList(anonymize) if e])

	def compareName(self, name):
		if name == None:
			return True

		nname = name.strip().lower()
		if nname == self.shortname.strip().lower():
			return True
		elif self.hostname.strip().lower().startswith(nname):
			return True
		else:
			return False

	def compareType(self, rtype):
		if rtype == None:
			return True

		if rtype.strip().lower() == self.type.strip().lower():
			return True
		else:
			return False

	def isDefault(self):
		""" Return true when the object does not represent a real router enty
		but a mere default values setting, which means line with * instead of
		router name and shortname.
		"""
		if self.compareName('*'):
			return True
		else:
			return False


def read_list(filename=DEVICE_LIST):
	""" Read host list from file and return iterator over group tuples. """

	defaults = {}
	rl = open(os.path.expanduser(filename), 'r')
	for l in rl.readlines():
		if l.lstrip().startswith("#"):
			continue
		if l.lstrip().startswith("//"):
			continue
		if l.strip() == '':
			continue

		hs = HostSpec(l, defaults)
		if hs.isDefault():
			defaults[hs.type] = hs
		else:
			yield hs


def filter_list(in_list, name=None, router_type=None, allow_disabled=False):
	""" Filter host list based onf name, type and disabled flag or any
	combination of these values.
	"""

	for r in in_list:
		if not allow_disabled and not r.enabled:
			continue
		if r.compareName(name) and r.compareType(router_type):
			yield r


def resolve_one_host(hostname, router_type=None, user=None, password=None, enablepassword=None, port=None, filename=None):
	""" Find HostSpec for the list of criterions, fill defaults and override additionals. """
	l = read_list(filename) if filename else read_list()
	hosts = list(filter_list(l, hostname, router_type))
	h = None
	if len(hosts) == 0:
		h = HostSpec()
		h.init(hostname,router_type,True,user,password,enablepassword)
	elif len(hosts) == 1:
		h = hosts[0].clone()
		if user:
			h.user = user
		if password:
			h.password = password
		if enablepassword:
			h.enablepassword = enablepassword
		if port:
			h.port = port
	else:
		raise Exception("Host name matching error. Matched "+str(len(hostgroups))+". Need to have single match.")

	if not h.type:
		raise Exception("Can not resolve host: Unknown host type.")
	if not h.hostname:
		raise Exception("Can not resolve host: No host specified.")

	return h



if __name__ == "__main__":
	raise Exception("This is a module with no directly executable code.")

