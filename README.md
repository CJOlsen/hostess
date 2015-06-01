# Hostess v0.1

Hostess is a small GUI program in early development that makes it easy to block and unblock websites.  Hostess exists to be a personal productivity tool, when you sit down to work it allows you to quickly block your favorite time-wasting websites and unblock them later.

When Hostess is blocking a website any requests to it will be redirected to 127.0.1.1 by the /etc/hosts file.  If you add www.example.com any web browser on your computer will find that www.example.com is unreachable.

## Requirements
* Debian or a feeling of adventure (tested with Debian 8 "Jessie")
* Python 3.x (tested with Python 3.4)

## Usage
* Download hostess.py and run from anywhere. ("python hostess.py" or "python3 hostess.py")
* You must have your password and sufficient privileges to order to edit the /etc/hosts file, generally this means you're in the sudoers list.

## Safety and Warnings
* This project is in early development, use at your own risk!
* Search the source code for 'os.system' to view the system calls.
* gksudo is used for authentication so Hostess never has access to your password.
* Hostess will ignore whatever is already in your hosts file, including sites your're already blocking.
* Hostess will attempt to back up your hosts file but you should also do that manually.

## Copyright
Christopher Olsen 2015

## License
GNU GPLv3
