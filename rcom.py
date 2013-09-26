#!/usr/bin/env python
#
# rat rcom - Router Automation Toolkit : remote communicator
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
This module does remote logins and it is writen in Python, not expect(!) indeed.
"""

# Global helpers and constants
BIN_SSH = "/usr/bin/ssh"
""" System specific SSH binary path. Usually /usr/bin/ssh . """

CONSOLE_LOGFORMAT = '%(message)s'
""" Logging format for console output. """

LOGFILE_LOGFORMAT = '%(asctime)-15s %(module)s:%(name)s: %(message)s'
""" Logging format for logfile output. """

SSH_EXPECT_NEWKEY='Are you sure you want to continue connecting'
""" Expect string form SSH binary when new SSH key is encountered. """

import pexpect
import sys
import logging
import struct, fcntl, termios
import traceback
import threading, os

import rlist

def get_term_size():
	""" Return tuple (rows,columns) representing current terminal. """
	w = struct.pack("HHHH", 0, 0, 0, 0)
	a = struct.unpack('hhhh', fcntl.ioctl(sys.stdout.fileno(), termios.TIOCGWINSZ , w))
	return (a[0],a[1])

setwinsize = None

def sigwinch(sig, data):
	""" React on signal SIGWINCH. """
	if setwinsize:
		try:
			setwinsize(*(get_term_size()))
		except:
			pass


class LogPipe(threading.Thread):
	def __init__(self, logger_name):
		"""
		Setup the object with a logger and a loglevel and start the thread.
		"""
		threading.Thread.__init__(self)
		self.daemon = False
		self.log = logging.getLogger(logger_name)
		self.fdRead, self.fdWrite = os.pipe()
		self.pipeReader = os.fdopen(self.fdRead)
		self.pipeWriter = os.fdopen(self.fdWrite, 'w')
		self.start()

	def fileno(self):
		"""
		Return the write file descriptor of the pipe.
		"""
		return self.fdWrite

	def write(self,*args):
		"""
		Pass write to the pipe below.
		"""
		self.pipeWriter.write(*args)

	def flush(self):
		"""
		Pass flush to the pipe below.
		"""
		self.pipeWriter.flush()

	def run(self):
		"""
		Run the logging thread. Log all incomming lines as debug.
		"""
		for line in iter(self.pipeReader.readline, ''):
			self.log.debug(line.strip('\n'))

	def close(self):
		"""
		Close the write end of the pipe.
		"""
		self.pipeWriter.close()



# Cisco support
def cisco_connect(host,user,password,enabpassword=None,command=None,output_handler=None,port=22,timeout=10):
	"""
	Connect and handle connection to a Cisco IOS.
	"""

	CISCO_EXPECT_PASSWORD='(P|p)assword:'
	CISCO_EXPECT_PROMPT = '\n[a-zA-Z0-9\._-]+(>|#)'

	# subroutine for setting window size on Cisco (which needs console interaction to do so)
	def cisco_setwinsize(rows, columns, session=None):
		log = logging.getLogger("cisco_setwinsize")
		if not session:
			global cisco_session
			session = cisco_session

		if not session:
			return

		log.debug("new rows="+str(rows)+" columns="+str(columns))

		session.sendline("terminal length "+str(rows))
		session.expect([CISCO_EXPECT_PROMPT])

		session.sendline("terminal width "+str(columns))
		session.expect([CISCO_EXPECT_PROMPT])


	def handle_ssh(s, log):
		y=0
		p=0
		while True:
			i=s.expect([SSH_EXPECT_NEWKEY, CISCO_EXPECT_PASSWORD,
				CISCO_EXPECT_PROMPT])
			if i==0:
				if y>1:
					raise Exception("SSH session failed: Can not save SSH key.")

				log.debug("New SSH key encountered. Sending yes to accept the key. This might impose a security risk. Please check the key.")
				s.sendline('yes')
				y+=1

			elif i==1:
				if p>1:
					raise Exception("Cisco session failed: Password not accepted.")

				log.debug("Sending password...")
				lf = s.logfile
				s.logfile = None
				s.sendline(password)
				s.logfile = lf
				p+=1
			elif i==2: # prompt
				log.debug("Got first prompt.")
				break


	def handle_enab(s, log, enabpassword):
		log.debug("Sending enable...")
		s.sendline("enable")
		i = s.expect([CISCO_EXPECT_PASSWORD, CISCO_EXPECT_PROMPT])
		if i==0:
			log.debug("Sending enable password...")
			lf = s.logfile
			s.logfile = None
			s.sendline(enabpassword)
			s.logfile = lf
			s.expect([CISCO_EXPECT_PROMPT])

		elif i==1: # shell
			log.debug("Got enabled prompt.")
			pass


	def run_command(s, log, command):
		cisco_setwinsize(0, 0, s)

		for l in command.splitlines():
			# remove empty commands
			if(l.strip() == ''):
				continue

			log.debug("Running command: "+l)
			s.sendline(l)
			while True:
				i=s.expect([CISCO_EXPECT_PROMPT])
				if(i==0): # prompt
					log.debug("Got prompt after command. before="+s.before)
					print "Got prompt after command. before="+s.before
					break
				elif(i==1): # anything to capture
					log.debug("Got output from command: <"+s.before+">")
					import re
					if re.match(CISCO_EXPECT_PROMPT,s.before):
						break
					if output_handler:
						log.debug("Calling output handler.")
						try:
							output_handler(command, s.before)
						except Exception as e:
							log.error("Output handler failed for command "+l+" "+traceback.format_exc())
					else:
						print s.before

		log.debug("Sending logout...")
		s.sendline('logout')
		s.expect(['\n'])


	def go_interactive(s, log):
		# set environment for cisco_setwinsize()
		global cisco_session
		cisco_session = s
		global setwinsize
		setwinsize = cisco_setwinsize

		# run setwinsize
		cisco_setwinsize(*(get_term_size()),session=s)
		log.info("Opening interactive session to "+host+":")
		sys.stdout.write(s.after)
		s.interact()





	if not host:
		Exception("Missing needed argument host.")

	if not user:
		Exception("Missing needed argument user.")

	if not password:
		Exception("Missing needed argument password.")

	log = logging.getLogger("cisco_connect")
	log.debug("Connecting to host "+host+" for user "+user+" port "+str(port))
	if command:
		log.debug("Going to run "+("(enabled)" if enabpassword else "(not enabled)")+" command(s): "+command)
	else:
		log.debug("Going to interactive mode "+("(enabled)" if enabpassword else "(not enabled)"))

	c = BIN_SSH+(' ' if port == 22 else ' -p'+str(port)+' ')+user+'@'+host
	log.debug("Spawning command "+c)
	s = pexpect.spawn(c,timeout=timeout)

	if log.isEnabledFor(logging.DEBUG):
		s.logfile = LogPipe("pexpect")

	# try block due to pexpect debugging which absolutely needs
	# to close the pipe in the end or the application locks down
	try:
		handle_ssh(s, log)

		if enabpassword:
			handle_enab(s,log,enabpassword)

		if command:
			run_command(s, log, command)
		else:
			go_interactive(s, log)
	finally:
		if s.logfile:
			s.logfile.close()
# end of cisco_connect

	

def main(argv):
	# setup logger
	log = logging.getLogger("remcomm")

	# set signal SIGWINCH handler
	import signal
	signal.signal(signal.SIGWINCH, sigwinch)

	# parse command line args
	import argparse
	parser = argparse.ArgumentParser(description='Line interface for remote routers.')
	parser.add_argument('-d', '--debug', action='store_const', dest='loglevel',
			const=logging.DEBUG, default=logging.INFO,
			help='enable debugging of pexpect and script flow')
	parser.add_argument('-l', '--log', action='store', dest='logfile',
			help='write log messages to logfile instead of stderr')
	parser.add_argument('-u', '--user', action='store', dest='user',
			help='manually override username instead of using configuration')
	parser.add_argument('-p', '--password', action='store', dest='password',
			help='manually override password instead of using configuration')
	parser.add_argument('-e', '--enable', action='store', dest='enabpass',
			help='manually override enable password instead of using configuration')
	parser.add_argument('-t', '--type', action='store', dest='router_type',
			help='manually override enable password instead of using configuration')
	parser.add_argument('-c', '--command', action='store', dest='command', nargs='?', default='',
			help='run command and exit, leave empty to let script read commands from stdin')
	parser.add_argument('-f', '--file', action='store', dest='filename',
			help='override device list file')

	parser.add_argument('host', help='host to interact with (short name, FQDN or IP address)')

	args = parser.parse_args(argv[1:])

	# setup logger
	if args.logfile:
		logging.basicConfig(level=args.loglevel,format=LOGFILE_LOGFORMAT,filename=args.logfile)
	else:
		logging.basicConfig(level=args.loglevel,format=CONSOLE_LOGFORMAT)

	if args.command == None: # command set to None when -c without args is present
		if os.isatty(sys.stdin.fileno()):
			print "Enter commands (Ctrl-D to finish):"
		# read commands from stdin
		args.command = ''.join(sys.stdin.readlines())
	if args.command == '': # default, no -c specified
		args.command = None

	# start command	
	try:
		rl = rlist.read_list(args.filename) if args.filename else rlist.read_list()
		hostgroups = list(rlist.filter_list(rl, args.host, None))
		if len(hostgroups) == 0:
			cisco_connect(args.host, args.user, args.password, args.enabpass, args.command)

		elif len(hostgroups) == 1:
			hostgroup = hostgroups[0]

			router_type = args.router_type if args.router_type else hostgroup[2]
			user = args.user if args.user else hostgroup[3]
			password = args.password if args.password else hostgroup[4]
			enabpass = args.enabpass if args.enabpass else hostgroup[5]

			cisco_connect(hostgroup[1], user, password, enabpass, args.command)

		else:
			raise Exception("Host name matching error. Matched "+str(len(hostgroups))+". Need to have single match.")
	except:
		log.error("Connect failed: "+traceback.format_exc())




if __name__ == "__main__":
	main(sys.argv)

