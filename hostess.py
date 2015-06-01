import tkinter as tk
import os, re, itertools


def backup():
    """
        Create a single backup of the hosts file the first time the program
        is run.  If the backup exists leave it alone.
    """
    p = os.path.join(os.path.expanduser('~'), '.hostess')
    os.makedirs(p, exist_ok=True)

    if 'hosts_backup_original' in os.listdir(p):
        ## TODO: add timestamp to backups
        os.system('cp /etc/hosts ~/.hostess/hosts_backup_recent')
    else:
        os.system('cp /etc/hosts ~/.hostess/hosts_backup_original')


class Counter(object):
    """
        Creates a helper object for keeping track of rows and columns during
        the window build.
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

    @staticmethod
    def new_from_host(host_line):
        """ Takes a line from the hosts file, returns a new Address object. """
        if re.search(r'(?<=^127.0.1.1\t).*', host_line):
            # currently blocked
            display = re.search(r'(?<=^127.0.1.1\t).*', host_line).group(0)
            blocked = True
            return Address(display=display, blocked=blocked)
        elif re.search(r'(?<=^\#127.0.1.1\t).*', host_line):
            # currently commented out in /etc/hosts
            display = re.search(r'(?<=^\#127.0.1.1\t).*', host_line).group(0)
            blocked = False
            return Address(display=display, blocked=blocked)
        else:
            return None # throw exception?
    
    @staticmethod
    def new_from_address(address):
        """ Takes a web address, creates and returns a new Address object. """
        # test if real web address
        return Address(display=address, blocked=True)
        
    def text(self):
        """
            Return ready to be written line for /etc/hosts, including tab
            and newline.
        """
        if self.blocked == True:
            return ''.join(['127.0.1.1\t', self.display, '\n'])
        else:
            ## unblocked means the line is commented out in /etc/hosts
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
        self.read()

    def read(self):
        f = open('/etc/hosts', 'r')
        hosts_list = f.readlines()
        self.backup = hosts_list
        f.close() # it isn't locked anyway...
        
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
            self.post_own = []
            self.managed = []
    
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

        print('self.pre_own: ', self.pre_own)
        print('pre_own: ', pre_own)
        print('post_own: ', post_own)
        print('owned: ', owned)
        
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
        

class Application(tk.Frame):
    """
        Main tkinter/GUI object.
    """
    
    def __init__(self, master=None):
        tk.Frame.__init__(self, master)
        self.grid()
        self.address_manager = HostsFileManager()
        self.create_widgets()
    
    def populate_listbox(self):
        # separated for DRYness
        for i in range(len(self.address_manager.managed)):
            address = self.address_manager.managed[i]
            self.address_window.insert("end",
                                       address.display)
            if address.blocked == True:
                self.address_window.select_set(i)

    def on_listbox_select(self, event):
        # for now, just set *all* select states from the address_window
        # TODO: find which one changed
        widget = event.widget
        #index = widget.curselection()[
        selections = widget.curselection()
        for i in range(len(self.address_manager.managed)):
            if i in selections:
                self.address_manager.managed[i].blocked = True
            else:
                self.address_manager.managed[i].blocked = False

    def create_widgets(self):
        """
            Build gui widgets and display them.
        """
        
        # these counters help keep track of row and column numbers during
        # the window build (can be a big help during interface changes)
        # row.current() gives the current row *without* incrementing the count
        # row.next() increments the count and returns the new value
        # row.reset(X) resets the row to X and returns X (useful for columns)
        row = Counter()
        col = Counter()
        
        # make widgets
        self.address_label = tk.Label(self, text="Blocked pages (Grey=blocked, White=not blocked)")
        self.address_window = tk.Listbox(self, selectmode="multiple", width=60)
        # populate Listbox
        self.populate_listbox()
        # make buttons
        self.save_button = tk.Button(self, text="Save",
                                     command=self.commit_changes)
        self.remove_button = tk.Button(self, text="Remove Selected",
                                       command=self.remove)
        self.add_new_button = tk.Button(self, text="Add New",
                                        command=self.add_new)
        self.add_new_text = tk.Entry(self)
        
        # display widgets
        self.address_label.grid(row=row.current(),
                                column=col.current())
        self.address_window.grid(row=row.next(),
                                 column=col.current(), columnspan=4)
        self.save_button.grid(row=row.next(),
                              column=col.current())
        self.remove_button.grid(row=row.current(),
                                column=col.next())
        self.add_new_button.grid(row=row.current(),
                                 column=col.next())
        self.add_new_text.grid(row=row.current(),
                               column=col.next())

        # bind events
        self.address_window.bind('<<ListboxSelect>>', self.on_listbox_select)

    def remove(self):
        """ Remove active item from listbox. web_url: string. """
        active = self.address_window.get("active")
        self.address_manager.remove(active)
        self.refresh()
    
    def add_new(self):
        """ Add new item to blocked list. """
        self.address_manager.new(self.add_new_text.get())
        self.refresh()

    def refresh(self):
        """ Refresh the address listbox with data from the address_manager """
        self.address_window.delete(0, "end")
        self.populate_listbox()
  
    def reset(self):
        """ Reload data from /etc/hosts """
        self.address_manager = HostsFileManager()
        self.refresh()

    def commit_changes(self):
        """ Gather data from gui and commit to /etc/hosts """
        self.address_manager.write()


backup()
app = Application()
app.master.title('Hostess')
app.mainloop()
