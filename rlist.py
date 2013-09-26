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

import logging
import traceback
import sys

import defaults

class ParseError(Exception):
	""" rlist parse exception class """
	def __init__(self,message,line):
		Exception.__init__(self,message+"on line: "+line)


def read_list(filename=defaults.DEVICE_LIST):
	""" Read router list from file and return iterator over group tuples. """

	rl = open(filename, 'r')
	for l in rl.readlines():
		if l.lstrip().startswith("#"):
			continue
		if l.lstrip().startswith("//"):
			continue
		if l.strip() == '':
			continue

		g = l.lstrip().split()
		if len(g) > 6:
			raise ParseError("Too much groups on line.", l)

		if len(g) < 3:
			raise ParseErrir("Too few groups on line.", l)

		yield g

def filter_list(in_list, name=None, router_type=None):
	""" Filter router list. """
	def compare_name(name, record):
		if name == None:
			return True

		nname = name.strip().lower()
		if nname == record[0].strip().lower():
			return True
		elif record[1].strip().lower().startswith(nname):
			return True
		else:
			return False

	def compare_type(rtype,record):
		if rtype == None:
			return True

		if rtype.strip().lower() == record[2].strip().lower():
			return True
		else:
			return False
	
	for r in in_list:
		if compare_name(name,r) and compare_type(router_type,r):
			yield r


def remove_pass(router_group):
	""" Replace passwords from router groups. """

	for i,ge in enumerate(router_group):
		if i == 4:
			yield '*'*len(ge)
		elif i == 5:
			yield '*'*len(ge)
		else:
			yield ge


def main(argv):
	# setup logger
	log = logging.getLogger("remcomm")

	# parse command line args
	import argparse
	parser = argparse.ArgumentParser(description='Line interface for remote routers.')
	parser.add_argument('-d', '--debug', action='store_const', dest='loglevel',
			const=logging.DEBUG, default=logging.INFO,
			help='enable debugging of pexpect and script flow')
	parser.add_argument('-l', '--log', action='store', dest='logfile',
			help='write log messages to logfile instead of stderr')
	parser.add_argument('-t', '--type', action='store', dest='type',
			help='manually override enable password instead of using configuration')
	parser.add_argument('-f', '--file', action='store', dest='filename',
			default=defaults.DEVICE_LIST, help='override device list file')
	parser.add_argument('-p', '--show-passwords', action='store_const', dest='showpass',
			const=True, default=False, help='shpow passwords in output')

	parser.add_argument('host', nargs="?", help='host to filter by name (short name or begining of FQDN)')

	args = parser.parse_args(argv[1:])
#	print str(args)
#	return

	# setup logger
	if args.logfile:
		logging.basicConfig(level=args.loglevel,format=defaults.LOGFILE_LOGFORMAT,filename=args.logfile)
	else:
		logging.basicConfig(level=args.loglevel,format=defaults.CONSOLE_LOGFORMAT)


	for rg in filter_list(read_list(args.filename), args.host, args.type):
		if args.showpass:
			print "\t".join(rg)
		else:
			print "\t".join(remove_pass(rg))


if __name__ == "__main__":
	main(sys.argv)

