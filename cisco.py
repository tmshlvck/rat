#!/usr/bin/env python
#
# rat cisco - Router Automation Toolkit : cisco support
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
This module does remote logins to a Cisco routers and it is writen in Python,
not expect(!) indeed.
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

import rcom

# Cisco support
class Cisco(rcom.DeviceOverSSH):
	"""
	Connect and handle connection to a Cisco IOS.
	"""

	EXPECT_PASSWORD='(P|p)assword:'
	EXPECT_PROMPT = '\n[a-zA-Z0-9\._-]+(>|#)'

	def __init__(self,host,user,password,enabpassword=None,port=22,timeout=10):
		rcom.DeviceOverSSH.__init__(self)
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
		self.setWinSize(*(rcom.get_term_size()))
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






if __name__ == "__main__":
	raise Exception("This is a module with no directly executable code.")

