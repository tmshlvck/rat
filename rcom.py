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
BIN_OPENSSH = "/usr/bin/ssh"
""" System specific SSH binary path. Usually /usr/bin/ssh . """

CONSOLE_LOGFORMAT = '%(message)s'
""" Logging format for console output. """

LOGFILE_LOGFORMAT = '%(asctime)-15s %(module)s:%(name)s: %(message)s'
""" Logging format for logfile output. """

import pexpect
import sys
import logging
import struct, fcntl, termios
import traceback
import threading, os

import rlist

def get_term_size():
	""" Return tuple (rows,columns) representing current terminal size. """
	w = struct.pack("HHHH", 0, 0, 0, 0)
	a = struct.unpack('hhhh', fcntl.ioctl(sys.stdout.fileno(), termios.TIOCGWINSZ , w))
	return (a[0],a[1])

class LogPipe(threading.Thread):
	"""
	Object that implements special pipe for logging module that emulates
	writing to file but instead it allows the program to filter the output.
	"""

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




class Device(object):
	def connect(self):
		pass

	def disconnect(self):
		pass

	def interact(self):
		pass

	def command(self,command,output_handler=None):
		pass

	def setWinSize(self,rows,columns):
		pass


class DeviceOverSSH(Device):
	SSH_EXPECT_NEWKEY='Are you sure you want to continue connecting'
	""" Expect string form SSH binary when new SSH key is encountered. """

	SSH_EXPECT_PASSWORD='(P|p)assword:'
	""" Expect string from SSH binary when password is needed. """

	def __init__(self):
		self.sess = None
		self.log = None

	def openSession(self, host, user, password, port=22, timeout=10):
		return self.openOpenSSHSession(host, user, password, port, timeout)

	def openOpenSSHSession(self, host, user, password, port=22, timeout=10):
		self.log.debug("Connecting to host "+host+" for user "+user+" port "+str(port))

		c = BIN_OPENSSH+' -p'+str(port)+' '+user+'@'+host
		self.log.debug("Spawning command "+c)
		self.sess = pexpect.spawn(c,timeout=timeout)

		if self.log.isEnabledFor(logging.DEBUG):
			self.sess.logfile = LogPipe("pexpect")


	def handleOpenSSH(self,next_stage_pattern):
		y=0
		p=0
		while True:
			i=self.sess.expect([self.SSH_EXPECT_NEWKEY,
					    self.SSH_EXPECT_PASSWORD,
					    next_stage_pattern])
			if i==0:
				if y>1:
					raise Exception("SSH session failed: Can not save SSH key.")

				self.log.debug("New SSH key encountered. Sending yes to accept the key. This might impose a security risk. Please check the key.")
				self.sess.sendline('yes')
				y+=1

			elif i==1:
				if p>1:
					raise Exception("SSH session failed: Password not accepted.")

				self.log.debug("Sending password...")
				lf = self.sess.logfile
				self.sess.logfile = None
				self.sess.sendline(self.password)
				self.sess.logfile = lf
				p+=1
			elif i==2: # next stage, in most cases prompt
				self.log.debug("Got next stage (prompt?) pattern.")
				break

	def handleSSH(self,next_stage_pattern):
		return self.handleOpenSSH(next_stage_pattern)

	
	def getExpectSession(self):
		return self.sess


# Cisco support
class Cisco(DeviceOverSSH):
	"""
	Connect and handle connection to a Cisco IOS.
	"""

	EXPECT_PASSWORD='(P|p)assword:'
	EXPECT_PROMPT = '\n[a-zA-Z0-9\._-]+(>|#)'

	def __init__(self,host,user,password,enabpassword=None,port=22,timeout=10):
		DeviceOverSSH.__init__(self)
		self.log = logging.getLogger("cisco")

		self.host = host
		self.user = user
		self.password = password
		self.enabpassword = enabpassword
		self.port = port
		self.timeout = timeout

	def closeDebugLog(self):
		if self.sess and self.sess.logfile:
				self.sess.logfile.close()

	def setWinSize(self, rows, columns):
		""" Subroutine for setting window size on Cisco
		(which needs console interaction to do so).
		"""

		if not self.log:
			raise Exception("Calling setWinSize() on object that has no initialized logger.")
		if not self.sess:
			raise Exception("Calling setWinSize() on object that has no initialized session.")

		self.log.debug("new rows="+str(rows)+" columns="+str(columns))

		self.sess.sendline("terminal length "+str(rows))
		self.sess.expect([self.EXPECT_PROMPT])

		self.sess.sendline("terminal width "+str(columns))
		self.sess.expect([self.EXPECT_PROMPT])


	def handleEnab(self):
		if not self.enabpassword:
			return

		self.log.debug("Sending enable...")
		self.sess.sendline("enable")
		i = self.sess.expect([self.EXPECT_PASSWORD, self.EXPECT_PROMPT])
		if i==0:
			self.log.debug("Sending enable password...")
			lf = self.sess.logfile
			self.sess.logfile = None
			self.sess.sendline(self.enabpassword)
			self.sess.logfile = lf
			self.sess.expect([self.EXPECT_PROMPT])

		elif i==1: # shell
			self.log.debug("Got enabled prompt.")


	def connect(self):
		if not self.host:
			Exception("Missing needed argument host.")

		if not self.user:
			Exception("Missing needed argument user.")

		if not self.password:
			Exception("Missing needed argument password.")

		try:
			self.openSession(self.host, self.user, self.password, self.port, self.timeout)
			self.handleSSH(self.EXPECT_PROMPT)
			self.handleEnab()
		except Exception as e:
				self.closeDebugLog()
				raise e


	def disconnect(self):
		try:
			if self.sess:
				self.log.debug("Sending logout...")
				self.sess.sendline('logout')
				self.sess.expect(['\n'])
		finally:
			self.closeDebugLog()



	def interact(self):
		# run setwinsize
		self.setWinSize(*(get_term_size()))
		self.log.info("Opening interactive session to "+self.host+":")
		sys.stdout.write(self.sess.after)
		self.sess.interact()


	def command(self,command,output_handler=None):
		self.setWinSize(0, 0)

		self.log.debug("Running command: "+command)
		self.sess.sendline(command)
		while True:
			i=self.sess.expect([self.EXPECT_PROMPT])
			if(i==0): # prompt
				self.log.debug("Got prompt after command. before="+s.before)
				print "Got prompt after command. before="+s.before
				break
			elif(i==1): # anything to capture
				self.log.debug("Got output from command: <"+s.before+">")
#				import re
#				if re.match(self.EXPECT_PROMPT,s.before):
#					break
				if output_handler:
					self.log.debug("Calling output handler.")
					try:
						output_handler(command, s.before)
					except Exception as e:
						self.log.error("Output handler failed for command "+l+" "+traceback.format_exc())
				else:
					print self.sess.before

###########################

# ProCurve support
class ProCurve(DeviceOverSSH):
	"""
	Connect and handle connection to a HP ProCurve switch.
	"""

	EXPECT_PASSWORD='(P|p)assword:'
	EXPECT_PROMPT = '[a-zA-Z0-9\._-]+(>|#)'
	EXPECT_PRESSANYKEY = '(P|p)ress any key to continue'
	EXPECT_YESNO = 'y/n'
	EXPECT_MORE = 'MORE'
	SEND_LOGOUT = 'logout'
	SEND_YES = 'y'
	

	def __init__(self,host,user,password,enabpassword=None,port=22,timeout=10):
		DeviceOverSSH.__init__(self)
		self.log = logging.getLogger("procurve")
		self.host = host
		self.user = user
		self.password = password
		self.enabpassword = enabpassword
		self.port = port
		self.timeout = timeout
		self.log = logging.getLogger("procurve")

	def closeDebugLog(self):
		if self.sess and self.sess.logfile:
				self.sess.logfile.close()

	def setWinSize(self, rows, columns):
		""" Subroutine for setting window size on Cisco
		(which needs console interaction to do so).
		"""

		if not self.log:
			raise Exception("Calling setWinSize() on object that has no initialized logger.")
		if not self.sess:
			raise Exception("Calling setWinSize() on object that has no initialized session.")

		self.log.debug("new rows="+str(rows)+" columns="+str(columns))

		self.sess.sendline("terminal length "+str(rows))
		self.sess.expect([self.EXPECT_PROMPT])

		self.sess.sendline("terminal width "+str(columns))
		self.sess.expect([self.EXPECT_PROMPT])

	def connect(self):
		
		if not self.host:
			Exception("Missing needed argument host.")

		if not self.user:
			Exception("Missing needed argument user.")

		if not self.password:
			Exception("Missing needed argument password.")

		try:
			self.openSession(self.host, self.user, self.password, self.port, self.timeout)
			self.handleSSH(self.EXPECT_PRESSANYKEY)
			# send any key and wait for prompt
			self.sess.sendline(' ')
			self.sess.expect([self.EXPECT_PROMPT])
			if self.enabpassword:
				self.handleEnab()
		except Exception as e:
				self.closeDebugLog()
				raise e



	def handleEnab(self):
		self.log.debug("Sending enable...")
		self.sess.sendline("enable")
		i = self.sess.expect([self.EXPECT_PASSWORD, self.EXPECT_PROMPT])
		if i==0:
			self.log.debug("Sending enable password...")
			lf = self.sess.logfile
			self.sess.logfile = None
			self.sess.sendline(self.enabpassword)
			self.sess.logfile = lf
			self.sess.expect([self.EXPECT_PROMPT])
		elif i==1: # shell
			self.log.debug("Got enabled prompt.")

	def command(self,command,output_handler=None):
		self.setWinSize(1000, 1920)

		self.log.debug("Running command: "+command)
		self.sess.sendline(command)
		output_start = False
		while True:
			i=self.sess.expect(['\n', self.EXPECT_PROMPT, self.EXPECT_MORE])
			if i == 0: # anything to capture
				output_start = True
		 		if output_handler:
		 			self.log.debug("Calling output handler.")
		 			try:
		 				output_handler(command, self.sess.before)
		 			except Exception as e:
		 				log.error("Output handler failed for command "+command+" "+traceback.format_exc())
				else:
					print self.sess.before
			elif i == 1: # prompt
				if output_start:
					self.log.debug("Got prompt after command.")
					break
				else:
					self.log.debug("Got prompt before command output. Ignore.")
		 	elif i == 2: # more
		 		self.log.debug("Sending space for more...")
		 		self.sess.send(' ')


	def disconnect(self):
		self.log.debug('Disconnecting from '+self.host+' .')
		try:
			if self.sess:
				self.log.debug("Sending logout...")
				self.sess.sendline(self.SEND_LOGOUT)
				c=0
				while True:
					c += 1
					if c > 10:
						raise Exception("Can not logout from ProCurve switch.")

					i = self.sess.expect([self.EXPECT_YESNO,
							      self.EXPECT_PROMPT,
							      pexpect.TIMEOUT,
							      pexpect.EOF])
					if i == 0:
						self.sess.sendline('y')
					elif i == 1:
						self.log.debug("Sending logout...")
						self.sess.sendline(self.SEND_LOGOUT)
					else:
						break
					
		finally:
			self.closeDebugLog()


	def interact(self):
		# run setwinsize
		self.setWinSize(*(get_term_size()))
		self.log.info("Opening interactive session to "+self.host+":")
		sys.stdout.write(self.sess.after)
		self.sess.interact()


# end of procurve support



device_session = None

def sigwinch(sig, data):
	""" React on signal SIGWINCH. """
	global device_session
	if device_session:
		try:
			device_session.setWinSize(*(get_term_size()))
		except:
			pass

def connect(router_type,host,user,password,enabpassword=None,port=22,timeout=10):
	nrt = router_type.strip()
	s = None
	if nrt == 'ios':
		s = Cisco(host,user,password,enabpassword,port,timeout)
		s.connect()
		
	elif nrt == 'procurve':
		s = ProCurve(host,user,password,enabpassword,port,timeout)
		s.connect()
	else:
		raise Exception("Unknown router type: "+nrt)

	# set global device_session for signal handler
	global device_session
	device_session = s

	return s

def main(argv):
	# setup logger
	log = logging.getLogger("rcom")

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
			help='override username instead of using configuration')
	parser.add_argument('-p', '--password', action='store', dest='password',
			help='override password instead of using configuration')
	parser.add_argument('-e', '--enable', action='store', dest='enabpass',
			help='override enable password instead of using configuration')
	parser.add_argument('-t', '--type', action='store', dest='router_type',
			help='override type, possible values: [ios,procurve]')
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
	rl = rlist.read_list(args.filename) if args.filename else rlist.read_list()
	hostgroups = list(rlist.filter_list(rl, args.host, None))
	if len(hostgroups) == 0:
		router_type = args.router_type
		host = args.host
		user = args.user
		password = args.password
		enabpass = args.enabpass

	elif len(hostgroups) == 1:
		hostgroup = hostgroups[0]

		# normalize hostgroup -> pad by None values
		for i in range(len(hostgroup),6):
			hostgroup.append(None)

		router_type = args.router_type if args.router_type else hostgroup[2]
		host = hostgroup[1]
		user = args.user if args.user else hostgroup[3]
		password = args.password if args.password else hostgroup[4]
		enabpass = args.enabpass if args.enabpass else hostgroup[5]
	else:
		log.error("Host name matching error. Matched "+str(len(hostgroups))+". Need to have single match.")
		return

	if not router_type:
		log.error("Can not connect: Unknown host type.")
		return
	if not host:
		log.error("Can not connect: No host specified.")
		return
	if not user:
		log.error("Can not connect: No user specified.")
		return
	if not password:
		# use blank password in that case... it might be ignored anyway
		password = ''

	ds = None
	try:
		ds = connect(router_type, host, user, password, enabpass)

		if args.command:
			log.debug("Going to run "+("(enabled)" if enabpass else "(not enabled)")+" command(s): "+args.command)
			ds.command(args.command)
		else:
			log.debug("Going to interactive mode "+("(enabled)" if enabpass else "(not enabled)"))
			ds.interact()
	except:
		log.error("Connect failed: "+traceback.format_exc())
	finally:
		if ds:
			ds.disconnect()





if __name__ == "__main__":
	main(sys.argv)

