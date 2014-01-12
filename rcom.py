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
	""" TODO """
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



def prepare_session(hostspec,port=22,timeout=10):
	"""
	TODO
	"""
	nrt = hostspec.type.strip()
	s = None
	if nrt == 'ios':
		if not hostspec.user:
			raise Exception("Can not connect: No user specified.")
		if not hostspec.password:
			# use blank password in that case... it might be ignored anyway
			hostspec.password = ''


		import cisco
		s = cisco.Cisco(hostspec.hostname,hostspec.user,hostspec.password,hostspec.enablepassword,port,timeout)
		
	elif nrt == 'procurve':
		import procurve
		s = procurve.ProCurve(hostspec.hostname,hostspec.user,hostspec.password,hostspec.enablepassword,port,timeout)
	else:
		raise Exception("Unknown router type: "+nrt)

	return s


if __name__ == "__main__":
	raise Exception("This is a module with no directly executable code.")

