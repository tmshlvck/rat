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
This module does remote logins to HP ProCurve boxes and it is writen
in Python, not expect(!) indeed.
"""

import pexpect
import sys
import logging
import traceback

import rcom

# ProCurve support
class ProCurve(rcom.DeviceOverSSH):
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
	

	def __init__(self,host,user,password,enabpassword=None,port=rcom.DEFAULT_SSH_PORT,timeout=rcom.DEFAULT_TIMEOUT):
		rcom.DeviceOverSSH.__init__(self)
		self.log = logging.getLogger("procurve")
		self.host = host
		self.user = user
		self.password = password
		self.enabpassword = enabpassword
		self.port = port
		if not self.port:
			self.port = rcom.DEFAULT_SSH_PORT
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
					output_start = True
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
		self.setWinSize(*(rcom.get_term_size()))
		self.log.info("Opening interactive session to "+self.host+":")
		sys.stdout.write(self.sess.after)
		self.sess.interact()




if __name__ == "__main__":
	raise Exception("This is a module with no directly executable code.")
