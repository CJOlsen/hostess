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
# """


import tkinter as tk
from model import HostsFileManager
from model import initialize


class Counter(object):
    """
    Creates a helper object for keeping track of rows and columns during
    the window build.
    """
    def __init__(self, start=0):
        object.__init__(self)
        self.count = start

    def current(self):
        """ :return: integer, current count. """
        return self.count

    def next(self):
        """ :return: integer, incremented current count. """
        self.count += 1
        return self.count

    def reset(self, start=0):
        """
        :param start: integer.  What to reset the count to.
                      (i.e. 3 for 3rd column)
        :return: int, new count
        """
        self.count = start
        return self.count


class SaveProfileDialog:
    """ Displayed when Save Profile is clicked on the File menu. """
    def __init__(self, master):
        self.top = tk.Toplevel(master)
        self.master = master
        
        tk.Label(self.top, text="Profile Name").pack()

        self.entry = tk.Entry(self.top)
        self.entry.pack(padx=5)

        ok_button = tk.Button(self.top, text="OK", command=self.on_ok)
        ok_button.pack(pady=5)

    def on_ok(self):
        """
        Called when OK button in dialog is clicked. Saves profile, closes self.

        :return: None
        """
        prof_name = self.entry.get()
        self.master.address_manager.save_profile(prof_name)

        self.top.destroy()


class LoadProfileDialog:
    """ Displayed when Load Profile is clicked on the File Menu. """
    def __init__(self, master, profile_names):
        """
        :param master: tkinter object that called this dialog
        :param profile_names: list of strings (profile names)
        :return:None
        """
        self.top = tk.Toplevel(master)
        self.master = master
        
        tk.Label(self.top, text="Profile Name").pack()

        self.options_listbox = tk.Listbox(self.top)
        for a in profile_names:
            self.options_listbox.insert("end", a)
        self.options_listbox.pack()
        
        ok_button = tk.Button(self.top, text="OK", command=self.on_ok)
        ok_button.pack(pady=5)

    def on_ok(self):
        """
        Called when OK is clicked in the dialog. Loads profile, closes self.

        :return: None
        """
        index = self.options_listbox.curselection()
        prof_name = self.options_listbox.get(index)
        self.master.address_manager.load_profile(prof_name)
        self.master.refresh()
        self.top.destroy()


class Application(tk.Tk):
    """ Main tkinter/GUI object. """

    def __init__(self, master=None):
        """
        :param master: None or tkinter object capable of being a master
                       (this is the top level object, so master isn't needed)
        :return: self
        """
        tk.Tk.__init__(self)
        self.grid()
        self.address_manager = HostsFileManager()
        self.session_backup = self.address_manager.backup

        # these are defined in create_widgets()
        self.address_label = None
        self.address_window = None
        self.save_button = None
        self.save_flag_label = None
        self.remove_button = None
        self.add_new_button = None
        self.add_new_text = None
        self.create_widgets()
        self.menubar = None
        self.filemenu = None
        self.create_menubar()
        
    def create_menubar(self):
        """
        Create menubar and submenu(s).

        :return: None
        """
        self.menubar = tk.Menu(self)
        self.filemenu = tk.Menu(self.menubar, tearoff=0)
        self.filemenu.add_command(label="Save Profile (not implemented)",
                                  command=self.on_save_profile)
        self.filemenu.add_command(label="Load Profile (not implemented)",
                                  command=self.on_load_profile)
        self.filemenu.add_separator()
        self.filemenu.add_command(label="Revert to beginning of session (not implemented)",
                                  command=self.on_revert_session)
        self.filemenu.add_command(label="Revert to pre-Hostess /etc/hosts (not implemented)",
                                  command=self.on_revert_all)
        self.filemenu.add_separator()
        self.filemenu.add_command(label="Close and Save",
                                  command=self.on_close_and_save)
        self.filemenu.add_command(label="Close",
                                  command=self.on_close)

        self.menubar.add_cascade(label="File", menu=self.filemenu)
        self.config(menu=self.menubar)

    def on_save_profile(self):
        """
        Called when Save Profile is clicked in the File menu.

        :return: None
        """
        a = SaveProfileDialog(self)

    def on_load_profile(self):
        """
        Called when Load Profile is clicked in the File menu.

        :return: None
        """
        names = self.address_manager.get_profile_names()
        a = LoadProfileDialog(self, names)  # The dialog displays itself

    def on_revert_session(self):
        """
        Revert to backup hosts file from beginning of session.

        :return: None
        """
        pass

    def on_revert_all(self):
        """
        Revert to backup hosts file from first time Hostess was run.

        :return: None
        """
        pass

    def on_close_and_save(self):
        """
        Saves changes to /etc/hosts and quits.

        :return: None
        """
        self.address_manager.write()
        # TODO: Check if the save was successful?  
        self.destroy()

    def on_close(self):
        """
        Discards changes and quits.

        :return: None
        """
        self.destroy()
    
    def populate_listbox(self):
        """
        Populates main url display listbox.

        Separated for DRYness.
        :return: None
        """
        for i in range(len(self.address_manager.managed)):
            address = self.address_manager.managed[i]
            self.address_window.insert("end",
                                       address.display)
            if address.blocked is True:
                self.address_window.select_set(i)

    def on_listbox_select(self, event):
        """
        Handle events thrown when the main listbox is clicked, event means
        something was selected or unselected.

        :param event: Bound to <<ListboxSelect>> events
        :return: None
        """
        # for now, just set *all* select states from the address_window
        # TODO: find which one changed instead of overwriting all of them
        widget = event.widget
        selections = widget.curselection()
        for i in range(len(self.address_manager.managed)):
            if i in selections:
                self.address_manager.managed[i].blocked = True
            else:
                self.address_manager.managed[i].blocked = False
        self.on_changed()

    def on_changed(self):
        """
        Displays an asterisk on the save button when there are unsaved changes.

        :return: None
        """
        self.save_button.config(text="Save*")
        
    def on_refreshed(self):
        """
        Clears the asterisk on the save button when there are no unsaved
        changes.

        :return: None
        """
        # Check if address_manager matches a fresh HostsFileManager        
        if self.address_manager == HostsFileManager():
            self.save_button.config(text="Save")
        else:
            self.save_button.config(text="Save**")

    def create_widgets(self):
        """
        Build gui widgets and display them.

        :return: None
        """

        # these counters help keep track of row and column numbers during
        # the window build (can be a big help during interface changes)
        # row.current() gives the current row *without* incrementing the count
        # row.next() increments the count and returns the new value
        # row.reset(X) resets the row to X and returns X (useful for columns)
        row = Counter()
        col = Counter()

        # make widgets
        self.address_label = tk.Label(self,
                                      text="Blocked pages (Grey=blocked, White=not blocked)")
        self.address_window = tk.Listbox(self, selectmode="multiple", width=60)
        # populate Listbox
        self.populate_listbox()
        # make buttons
        self.save_button = tk.Button(self, text="Save",
                                     command=self.on_click_save)
        self.remove_button = tk.Button(self, text="Remove Selected",
                                       command=self.on_click_remove)
        self.add_new_button = tk.Button(self, text="Add New",
                                        command=self.on_click_add_new)
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

    def on_click_add_new(self):
        """
        Add new item to blocked list.

        :return: None
        """
        self.address_manager.new(self.add_new_text.get())
        self.refresh()
        self.on_changed()

    def refresh(self):
        """
        Refresh the address listbox with data from the address_manager.

        :return: None
        """
        self.address_window.delete(0, "end")
        self.populate_listbox()
        self.on_refreshed()

    def reset(self):
        """
        Reload data from /etc/hosts

        :return: None
        """
        self.address_manager = HostsFileManager()
        self.refresh()

    def on_click_remove(self):
        """
        Remove active item from listbox. web_url: string.

        :return: None
        """
        active = self.address_window.get("active")
        self.address_manager.remove(active)
        self.refresh()
        self.on_changed()
        
    def on_click_save(self):

        """
        Gather data from gui and commit to /etc/hosts

        :return: None
        """
        self.address_manager.write()
        self.refresh()


initialize()
app = Application()
app.title('Hostess')
app.mainloop()
