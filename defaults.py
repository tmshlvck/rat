#!/usr/bin/env python
#
# rat defaults - Router Automation Toolkit
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
This module contains default constants and helpers.
"""

# Global helpers and constants
DEVICE_LIST = "device-list.conf"
""" Path to the text list of devices. Usually /etc/rat/device-list.txt . """

BIN_SSH = "/usr/bin/ssh"
""" System specific SSH binary path. Usually /usr/bin/ssh . """

CONSOLE_LOGFORMAT = '%(message)s'
""" Logging format for console output. """

LOGFILE_LOGFORMAT = '%(asctime)-15s %(module)s:%(name)s: %(message)s'
""" Logging format for logfile output. """



if __name__ == "__main__":
	raise Exception("This module does not contain any self-contained code.")

