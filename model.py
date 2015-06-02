# Author: Christopher Olsen
# Copyright: 2015
# Title: Hostess
# Version: 0.1 (active development/testing)
#
# License:
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


import os
import io
import re
import json

def backup():
    """
        Create a single backup of the hosts file the first time the program
        is run.  If the backup exists leave it alone.
    """
    p = os.path.join(os.path.expanduser('~'), '.hostess')
    os.makedirs(p, exist_ok=True)

    if 'hosts_backup_original' in os.listdir(p):
        # TODO: add timestamp to backups
        os.system('cp /etc/hosts ~/.hostess/hosts_backup_recent')
    else:
        os.system('cp /etc/hosts ~/.hostess/hosts_backup_original')


def initialize():
    """ Runs when Hostess is started. """
    backup()
    p = os.path.join(os.path.expanduser('~'), '.hostess/profiles.json')
    
    open(p, 'a').close() # creates the profiles.json file if it doesn't exist
    # if the profiles.json file is empty put an empty json dictionary in it
    if os.stat(p).st_size == 0:
        f = open(p, 'w')
        f.write(json.dumps({}))
        f.close()


class Address(object):
    """
        Holds the websites being blocked.
        Attributes:
        display: string, display name of the website.
        blocked: boolean, is the website currently blocked?
        Methods:
        text: Returns a string ready for writing to /etc/hosts
        Class Methods:
        new_from_hosts: takes a string of the form
            "#127.0.1.1\twww.example.com\n" and builds a new Address object
        new_from_address: takes a string of the form "www.example.com" and
            builds a new Address object
        
    """
    def __init__(self, display, blocked=True):
        self.display = display
        self.blocked = blocked
        
    def __eq__(self, other):
        return self.__dict__ == other.__dict__
    
    @classmethod
    def new_from_host(cls, host_line):
        """ Takes a line from the hosts file, returns a new Address object. """
        if re.search(r'(?<=^127.0.1.1\t).*', host_line):
            # currently blocked
            display = re.search(r'(?<=^127.0.1.1\t).*', host_line).group(0)
            blocked = True
            return cls(display=display, blocked=blocked)
        elif re.search(r'(?<=^\#127.0.1.1\t).*', host_line):
            # currently commented out in /etc/hosts
            display = re.search(r'(?<=^\#127.0.1.1\t).*', host_line).group(0)
            blocked = False
            return cls(display=display, blocked=blocked)
        else:
            return None  # throw exception?

    @classmethod
    def new_from_address(cls, address, blocked=True):
        """ Takes a web address, creates and returns a new Address object. """
        # test if real web address
        return cls(display=address, blocked=blocked)

    def text(self):
        """
            Return ready to be written line for /etc/hosts, including tab
            and newline.
        """
        if self.blocked == True:
            return ''.join(['127.0.1.1\t', self.display, '\n'])
        else:
            # self.blocked == False means the line is commented out in /etc/hosts
            return ''.join(['#127.0.1.1\t', self.display, '\n'])

    def set_blocked(self):
        """ Set the blocked attribute to true. """
        self.blocked = True

    def set_unblocked(self):
        """ Set the blocked attribute to false. """
        self.blocked = False


class HostsFileManager(object):
    """
        Object to house all the data from the /etc/hosts file

        Attributes:
        backup: list of hosts file as read in (each line is an item)
        pre_own: list of portion of hosts file before Hostess owned lines
        post_own: list....after Hostess owned lines
        managed: list of Address objects of managed web addresses

    """

    def __init__(self):
        """ Parse the /etc/hosts file and store data in this object. """
        object.__init__(self)
        self.backup = None
        self.pre_own = []
        self.post_own = []
        self.managed = []
        self.read()
        self.profile_name = None

        self.profiles_path = os.path.join(os.path.expanduser('~'),
                                          '.hostess/profiles.json')

    def __eq__(self, other):
        """ Override equality comparison, used to check if file state matches
            GUI/controller state. """
        # the backup attributes must be filtered out because if the file
        # has changed they'll be different
        return {k: v for k, v in self.__dict__.items() if k != "backup"} \
               == {k: v for k, v in other.__dict__.items() if k != "backup"}
        
    def read(self):
        f = open('/etc/hosts', 'r')
        hosts_list = f.readlines()
        self.backup = hosts_list
        f.close()  # it isn't locked anyway...

        if '# begin Hostess ownership\n' in hosts_list:
            start_ownership = hosts_list.index('# begin Hostess ownership\n')
            end_ownership = hosts_list.index('# end Hostess ownership\n')

            # save everything before and after the ownership tags
            self.pre_own = hosts_list[:start_ownership]
            self.post_own = hosts_list[end_ownership+1:]
            owned_raw = hosts_list[start_ownership+1:end_ownership]
            self.managed = [Address.new_from_host(a) for a in owned_raw]
        else:
            self.pre_own = hosts_list

    def write(self):
        """
            Assemble the text file, write to temp directory, then use
            gksudo to get write privileges to /etc/hosts.
        """
        def handle_newlines(x):
            if x != '\n':
                ''.join([x, '\n'])
            else:
                '\n'
        pre_own = [handle_newlines(a)
                   for a
                   in self.pre_own]
        post_own = [handle_newlines(a)
                    for a
                    in self.post_own]
        owned = [a.text() for a in self.managed]

        out_list = []
        if len(self.pre_own) > 0:
            for i in self.pre_own:
                out_list.append(i)
        if len(owned) > 0:
            out_list.append('# begin Hostess ownership\n')
            for i in owned:
                out_list.append(i)
            out_list.append('# end Hostess ownership\n')
        if len(self.post_own) > 0:
            for i in self.post_own:
                out_list.append(i)

        out_text = ''.join(out_list)
        outfile = open('/tmp/temp_hosts.tmp', 'wt')
        outfile.write(out_text)
        outfile.close()

        os.system('gksudo mv /tmp/temp_hosts.tmp /etc/hosts')

    def new(self, address):
        """ Takes a web address and adds it to the managed list. """
        self.managed.append(Address.new_from_address(address))

    def remove(self, address):
        """ Takes a web address and removes it from the managed list. """
        self.managed = list(filter(lambda x: x.display != address, self.managed))

    def save_profile(self, profile_name):
        """ Saves current profile. """
        address_list = []
        for address in self.managed:
            address_list.append({"display": address.display,
                                 "blocked": address.blocked})
            
        profiles_file = open(self.profiles_path, 'r')  # open file
        profiles = json.load(profiles_file)       # un-jsonify
        profiles[profile_name] = address_list     # set profile data (overwrites!)
        profiles_file.close()                     # close read version
        profiles_file = open(self.profiles_path, 'w') # open write version
        json.dump(profiles, profiles_file)        # jsonify and write
        profiles_file.close()                     # close file
        
        self.profile_name = profile_name
    
    def load_profile(self, profile_name):
        """ Loads a profile from ~/.hostess/ matching profile_name. """
        p_file = open(self.profiles_path)
        p = json.load(p_file)
        p_file.close()

        self.managed = []
        self.profile_name = profile_name
        for address in p[profile_name]:
            self.managed.append(Address.new_from_address(address["display"],
                                                         address["blocked"]))

    def get_profile_names(self):
        p_file = open(self.profiles_path)
        p = json.load(p_file)
        p_file.close()
        return p.keys()
        
    
    def revert_session(self, session_backup):
        """ Reverts to backup of /etc/hosts at the beginning of the session """
        pass

    def revert_to_pre_hostess(self):
        pass
