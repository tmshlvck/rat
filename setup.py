#!/usr/bin/env python
#
# rat-list - Router Automation Toolkit: router list manager script
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


from distutils.core import setup

setup(
    name = 'rat',
    version = '0.1',
    description = 'Router Administration Toolkit',
    author = 'Tomas Hlavacek',
    author_email = 'tmshlvck@gmail.com',
    url = 'https://github.com/tmshlvck/rat',
    packages = ['rat'],
    scripts = ['rat-list', 'rat-com'],
    long_description = """Router Administration Toolkit - toolkit for
establishing and making use of connection with various routers. The toolkit
supports both Python objective as well as command-line interfaces.
"""
      )
