import tkinter as tk
import os, re


def backup():
    """
        Create a single backup of the hosts file the first time the program
        is run.  If the backup exists leave it alone.
    """
    p = os.path.join(os.path.expanduser('~'), '.hostess')
    os.makedirs(p, exist_ok=True)

    if 'hosts_backup_original' in os.listdir(p):
        os.system('cp /etc/hosts ~/.hostess/hosts_backup_recent')
    else:
        os.system('cp /etc/hosts ~/.hostess/hosts_backup_original')


class Counter(object):
    """
        Creates a helper object for keeping track of rows and columns during
        the window build
    """
    
    def __init__(self, start=0):
        object.__init__(self)
        self.count = start
    def current(self):
        return self.count
    def next(self):
        self.count += 1
        return self.count
    def reset(self, start=0):
        self.count = start
        return self.count


class Address(object):
    """
        Holds the websites being blocked.
        Attributes:
        display: strong.  display name of the website.
        blocked: boolean.  Is the website currently blocked?
        Methods:
        text: Returns a string ready for writing to /etc/hosts
    """
    
    def __init__(self, raw_text):
        if re.search(r'(?<=^127.0.1.1\t).*', a).group(0):
            self.display = re.search(r'(?<=^127.0.1.1\t).*', a).group(0)
            self.blocked = True
        elif re.search(r'(?<=^\#127.0.1.1\t).*', a).group(0):
            self.display = re.search(r'(?<=^\#127.0.1.1\t).*', a).group(0)
            self.blocked = False
        else:
            return None # throw exception?

    def text(self):
        """ return ready to be written to /etc/hosts """
        if self.blocked == True:
            return ''.join(['127.0.1.1\t', self.display, '\n'])
        else:
            ## unblocked means the line is commented out in /etc/hosts
            return ''.join(['#127.0.1.1\t', self.display, '\n'])


class HostsFile(object):
    """
        Object to house all the data from the /etc/hosts file

        Attributes:
        backup: list of hosts file as read in (each line is an item)
        pre_own: list of portion of hosts file before Hostess owned lines
        post_own: list....after Hostess owned lines
        blocked: list of web urls that are currently being sent to 127.0.1.1
        unblocked: list of web urls that are commented out in /etc/hosts
    """
    def __init__(self):
        """ Parse the /etc/hosts file and store data in this object. """
        object.__init__(self)

        f = open('/etc/hosts', 'r')
        hosts_list = f.readlines()
        self.backup = hosts_list
        f.close() # it isn't locked anyway...can gksudo be used at open time?
        
        if '# begin Hostess ownership\n' in hosts_list:
            start_ownership = hosts_list.index('# begin Hostess ownership\n')
            end_ownership = hosts_list.index('# end Hostess ownership\n')

            # save everything before and after the ownership tags
            self.pre_own = hosts_list[:start_ownership]
            self.post_own = hosts_list[end_ownership+1:]
            owned = hosts_list[start_ownership+1:end_ownership]
        else:
            self.pre_own = hosts_list
            self.post_own = []
            owned = []
        
        # blocked and unblocked sites are kept as web urls
        self.blocked = [re.search(r'(?<=^127.0.1.1\t).*', a).group(0)
                        for a
                        in owned
                        if re.search(r'(?<=^127.0.1.1\t).*', a)]
        self.unblocked = [re.search(r'(?<=\#127.0.1.1\t).*', a).group(0)
                          for a
                          in owned
                          if re.search(r'(?<=\#127.0.1.1\t).*', a)]

        print("\nblocked: ", self.blocked)
        print("\nunblocked: ", self.unblocked)
        

    def write(self):
        """
            Assemble the text file, write to temp directory, then use
            gksudo to get write privileges to /etc/hosts.
        """
        pre_own = [''.join([a, '\n'])
                   for a
                   in self.pre_own]
        post_own = [''.join([a, '\n'])
                    for a
                    in self.post_own]
        blocked = [''.join(['127.0.1.1\t', a, '\n'])
                   for a
                   in self.blocked]
        unblocked = [''.join(['#127.0.1.1\t', a, '\n'])
                     for a
                     in self.blocked]
        
        if len(post_own) == 0 and len(blocked) == 0 and len(unblocked) == 0:
            out_text = pre_own
        else:
            out_text = ''.join([pre_own,
                                '# begin Hostess ownership\n',
                                blocked, unblocked,
                                '# end Hostess ownership\n',
                                post_own])

        outfile = open('/tmp/temp_hosts.tmp', 'wt')
        outfile.write(out_text)
        outfile.close()

        os.system('gksudo mv /tmp/temp_hosts.tmp /etc/hosts')
        
    def add_blocked(self, address):
        self.blocked.append(address)

    def add_unblocked(self, address):
        self.unblocked.append(address)

    def remove_blocked(self, address):
        self.blocked = filter(lambda x: x != address,
                              self.blocked)
        
    def remove_unblocked(self, address):
        self.unblocked = filter(lambda x: x != address,
                                self.unblocked)

    def blocked_to_unblocked(self, address):
        self.remove_blocked(address)
        self.add_unblocked(address)

    def unblocked_to_blocked(self, address):
        self.remove_unblocked(address)
        self.add_blocked(address)


class Application(tk.Frame):
    """
        Main tkinter object.
    """
    
    def __init__(self, master=None):
        tk.Frame.__init__(self, master)
        self.grid()
        self.hosts = HostsFile()
        self.create_widgets()
        
    def create_widgets(self):
        """
            Build gui widgets and display them.
        """
        
        # these counters help keep track of row and column numbers during
        # the window build
        # row.current() gives the current row *without* incrementing the count
        # row.next() increments the count and returns the new value
        # row.reset(X) resets the row to X and returns X (useful for columns)
        row = Counter()
        col = Counter()
        
        # make widgets
        self.blocked_label = tk.Label(self, text="Blocked pages")
        self.blocked_window = tk.Listbox(self, selectmode="multiple")
        for i in self.hosts.blocked:
            self.blocked_window.insert("end", i)

        self.remove_button = tk.Button(self, text="Remove selected",
                                       command=self.remove)
        self.add_new_button = tk.Button(self, text="Add new",
                                        command=self.add_new)
        self.add_new_text = tk.Entry(self)

        self.move_down_button = tk.Button(self, text="Unblock Selected")
        self.move_up_button = tk.Button(self, text="Block Selected")
        
        self.unblocked_label = tk.Label(self, text="Unblocked pages")
        self.unblocked_window = tk.Listbox(self, selectmode="multiple")
        for j in self.hosts.unblocked:
            self.unblocked_window.insert("end", j)

        self.save_button = tk.Button(self,
                                    text="Save Changes",
                                    command=self.commit_changes)
        self.reset_button = tk.Button(self,
                                     text="Reset",
                                     command=self.reset)
        
        # display widgets
        self.blocked_label.grid(row=row.current(),
                                column=col.current())
        self.blocked_window.grid(row=row.next(),
                                 column=col.current(), columnspan=3)
        self.remove_button.grid(row=row.next(),
                                column=col.current())
        self.add_new_button.grid(row=row.current(),
                                 column=col.next())
        self.add_new_text.grid(row=row.current(),
                               column=col.next())
        col.reset()
        self.move_down_button.grid(row=row.next(),
                                   column=col.current())
        self.move_up_button.grid(row=row.current(),
                                 column=col.next())
        col.reset()
        self.unblocked_label.grid(row=row.next(),
                                  column=col.current())
        self.unblocked_window.grid(row=row.next(),
                                   column=col.current(), columnspan=3)
        self.save_button.grid(row=row.next(), column=col.current())
        self.reset_button.grid(row=row.current(), column=col.next())
        
    def remove(self, web_url):
        """ Remove item from blocked list. web_url: string. """
        self.blocked = filter(lambda x: x != web_url, self.blocked)
        
    def add_new(self, web_url):
        """ Add new item to blocked list. web_url: string. """
        self.blocked.append(web_url)
    
    def move_down(self, web_url):
        """
            Delete item from blocked list and add it to ublocked list.
            web_url: string.
        """
        self.blocked = filter(lambda x: x != web_url, self.blocked)
        self.unblocked.append(web_url)
    
    def move_up(self):
        """
            Delete item from blocked list and add it to ublocked list.
            web_url: string.
        """
        self.unblocked = filter(lambda x: x != web_url, self.blocked)
        self.blocked.append(web_url)
    
    def reset(self):
        """ Reload data from /etc/hosts """
        pass

    def commit_changes(self):
        """ Gather data from gui and commit to /etc/hosts """
        #self.blocked = 
        self.hosts.write()

backup()
app = Application()
app.master.title('Hostess')
app.mainloop()
