#! /usr/bin/python

# Title: qsl
# Description: module to upload/download adif files
# Author: Ante Laurijssen VA2BBW <va2bbw@gmail.com>
# Date Created (yyyy-mm-dd): 2014-06-20
# Version: 0.9
# Copyright: (C) 2014 Ante Laurijssen
# Licence: GPLv3

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""
This module contains all the necessary code to sign adif files, upload and 
download them to and from LoTW, eqsl.cc and ClubLog.
"""

# ==============================================================================

# imports

import subprocess
import getpass
import time

# global variables

# classes

class Lotw(object):
    def __init__(self, log):
        self.log = log
        self.tq8 = log + ".tq8"
        self.location = ""

    def log_sign(self):
        if self.location == "":
            self.location = eval(input("Please enter the TQSL station location to be used: "))
        pw = getpass.getpass("Please enter your TQSL password: ")
        subprocess.call("tqsl -d -a compliant -l %s -p %s %s -o %s -x" % (self.location, pw, self.log, self.tq8))
        print(("Signing log %s..." % (self.log)))
        time.sleep(3)

    def log_upload(self):
        choice = 0
        while choice != "y" and choice != "n":
            choice = eval(input("Upload log %s to LoTW? (y/n): " % (self.tq8)))
        if choice == "n":
            print(("Log % not uploaded..." % (self.tq8)))
        elif choice == "y":
            subprocess.call("tqsl -u -l %s %s -x" % (self.location, self.tq8))
            print(("Uploading log %s to LoTW..." % (self.tq8)))
            time.sleep(3)

    def log_download(self):
        uname = eval(input("Please enter your LoTW user name: "))
        pw = getpass.getpass("Please enter your LoTW password: ")

class Eqsl(object):
    def __init__(self, log):
        self.log = log

    def log_upload(self):
        choice = 0
        while choice != "y" and choice != "n":
            choice = eval(input("Upload log %s to eqsl.cc? (y/n): " % (self.log)))
        if choice == "n":
            print(("Log % not uploaded..." % (self.log)))
        elif choice == "y":
            print(("Uploading log %s to eqsl.cc..." % (self.log)))
            time.sleep(3)

    def log_download(self):
        uname = eval(input("Please enter your eqsl.cc user name: "))
        pw = getpass.getpass("Please enter your eqsl.cc password: ")

class Clublog(object):
    def __init__(self, log):
        self.log = log
        
    def log_upload(self):
        uname = eval(input("Please enter your Clublog user name: "))
        pw = getpass.getpass("Please enter your Clublog password: ")

# functions

# main function

def main():
    print("Nothing implemented as main function, this is to be used as a module")

# This calls the functions to start the script

if __name__ == "__main__":
    main()
