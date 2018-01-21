#! /usr/bin/python

# Title: SimPyL
# Description: Simple Python Logger
# Author: Ante Laurijssen VA2BBW <va2bbw@gmail.com>
# Date Created (yyyy-mm-dd): 2014-05-19
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
SimPyL - The Simple Python Logger

A simple console-based logging program for ham radio operators. 

After learning the basics of the python programming language, I was trying to
come up with a coding project that would give me the opportunity to learn and
to create something simple and useful for me and my fellow hams. As time goes
on and as my knowledge progresses, more features will be added. My hope is that
one day this piece of software becomes robust and complete enough to be used
as an every day logger for ham radio operators, as well as a contest logger.
"""

# ==============================================================================

# python module imports

from __future__ import absolute_import

import os
import sys

try:
    import readline
except ImportError:
    print("Module \"readline\" not available.")

import collections
import re
import prettytable
import sqlite3
import ConfigParser
import datetime
import time

# my module imports

import cty_dat_parser
import qsl

# global variables

simpyl_version = "v.0.9"
home_folder = os.path.expanduser("~") + "/.simpyl"
    
# configuration parser

Config = ConfigParser.ConfigParser()
Config.read(home_folder + "/simpyl.conf")
Config.sections()

def ConfigSectionMap(section):
    dict1 = {}
    options = Config.options(section)
    for option in options:
        try:
            dict1[option] = Config.get(section, option)
            if dict1[option] == -1:
                DebugPrint("skip: %s" % option)
        except:
            print("exception on %s!" % option)
            dict1[option] = None
    return dict1

# classes

class Log(object):
    """
    Log class definition. This handles all the functions and attributes related to the chosen log database
    """
    def __init__(self):
        self.name = ""
        self.call = ""
        self.qso_fields = tuple(ConfigSectionMap("QSOFields")["qso_fields"].split("\n"))
        self.db = ""
        self.c = ""
        self.import_fields = tuple(ConfigSectionMap("ADIFImportedFields")["import_fields"].split("\n"))
        self.visible_fields = tuple(ConfigSectionMap("VisibleFields")["visible_fields"].split("\n"))

    def choose(self):
        """
        This method prompts the user to choose his log file, and also opens the sqlite3 connecion to that log database.
        """
        self.name = raw_input("\nPlease choose a log file (type 'l' for list) : ")
        while self.name == "":
            self.choose()
        if self.name == "l":
            for f in os.listdir(home_folder):
                if f.endswith(".db"):
                    print("\n" + f)
            self.name = ""
            self.choose()
        elif self.name.endswith(".db"):
            if self.name in os.listdir(home_folder):
                self.connect()
                print("\nYou have chosen: %s" % (self.name))
                enter()
                start_main_menu()
            else:
                choice = 0
                while choice != "y" and choice != "n":
                    choice = raw_input("\nLog %s does not exist. Would you like to create it? (y/n): " % (self.name))
                if choice == "n":
                    print("\nLog %s not created" % (self.name))
                    self.choose()
                elif choice == "y":
                    self.connect()
                    print("\nLog %s created! " % (self.name))
                    start_main_menu()
        else:
            self.name = self.name + ".db"
            if self.name in os.listdir(home_folder):
                self.connect()
                print("\nYou have chosen: %s" % (self.name))
                enter()
                start_main_menu()
            else:
                choice = 0
                while choice != "y" and choice != "n":
                    choice = raw_input("\nLog %s does not exist. Would you like to create it? (y/n): " % (self.name))
                if choice == "n":
                    print("\nLog %s not created" % (self.name))
                    self.choose()
                elif choice == "y":
                    self.connect()
                    print("\nLog %s created! " % (self.name))
                    start_main_menu()

    def format_fields(self, l):
        """
        This method formats lists or tuples into a string. This is sometimes the only way a list
        or tuple of fields can be passed to a SQL statement.
        """
        s = str(l).replace("'", "").replace("(", "").replace(")", "").replace("\"", "")
        return s

    def connect(self):
        """
        This method connects to the database (creates it if it doesn't exist) and creates the cursor.
        """
        self.db = sqlite3.connect("%s/%s" % (home_folder, self.name))
        self.db.row_factory = sqlite3.Row
        self.c = self.db.cursor()
        self.create_table()
        
    def create_table(self):
        """
        This creates the table for new database files if it doesn't exist.
        """
        self.c.execute("CREATE TABLE IF NOT EXISTS log(Operator TEXT DEFAULT '{o}' COLLATE NOCASE)".format(o = self.call))
        for field in self.qso_fields:
            try:
                self.c.execute("ALTER TABLE log ADD COLUMN {f} TEXT COLLATE NOCASE".format(f = field))
            except sqlite3.OperationalError:
                pass
            self.db.commit()
        for field in self.visible_fields:
            try:
                self.c.execute("ALTER TABLE log ADD COLUMN {f} TEXT COLLATE NOCASE".format(f = field))
            except sqlite3.OperationalError:
                pass
            self.db.commit()

    def choose_call(self):
        """
        Prompts the user to enter his callsign and stores the value in the my_log Log instance.
        """
        if self.call == "":
            while self.call == "":
                self.call = raw_input("\nPlease enter your callsign: ").upper()
            start_main_menu()
        else:
            self.call = raw_input("\nPlease enter new callsign: ").upper()
        start_main_menu()

    def add_qso(self):
        """
        This method will prompt the user for QSO informaion and write it to the database.
        """
        qso_data = []
        for field in self.qso_fields:
            data = raw_input("\n%s (default: *): " % (field)).upper()
            qso_data.append(data)
        self.check(dict(zip(self.qso_fields, qso_data)))
        qso_data_rows = []
        qso_data_rows.append(qso_data)
        my_table = Table("New QSO", self.qso_fields, qso_data_rows)
        print(my_table.draw())
        choice = 0
        while choice != "" and choice != "c":
            choice = raw_input("\nPress enter to write QSO to database or 'c' to cancel: ")
        if choice == "c":
            print("\nThis new QSO has not been entered")
            enter()
        elif choice == "":
            self.c.execute("INSERT INTO log {f} VALUES {d}".format(f = self.qso_fields, d = tuple(qso_data)))
            self.db.commit()
        log_menu.draw()
        
    def search_call(self):
        """
        This method searches for the specified callsign in the QSO database and returns all the QSOs.
        The info is then used to create a pretty table showing the QSOs.
        """
        call = raw_input("\nPlease enter a callsign to search: ").upper()
        clear_screen()
        rows = []
        for row in self.c.execute("SELECT {f} FROM log WHERE Call = ? ORDER BY QSO_Date DESC, Time_On DESC".format(f = self.format_fields(self.visible_fields)), (call,)):
            rows.append(row)
        my_table = Table("QSOs with %s" % (call), self.visible_fields, rows)
        print(my_table.draw())
        enter()
        log_menu.draw()

    def last_five(self):
        """
        This method searches for the last 5 QSOs in the database and sends them to a pretty table
        to be drawn on-screen.
        """
        rows = []
        for row in self.c.execute("SELECT {f} FROM log ORDER BY QSO_Date DESC, Time_On DESC LIMIT 5".format(f = self.format_fields(self.visible_fields))):
            rows.append(row)
        my_table = Table("Last 5 QSOs", self.visible_fields, rows)
        print(my_table.draw())

    def adif_parse(self, fn):
        """
        This method is used to parse through an ADIF file and return a list of dictionaries. 
        This code was modified by me, but the original was written by OK4BX.
        """
        raw = re.split('<eor>|<eoh>(?i)',open(fn).read() )
        raw.pop(0)  #remove header
        raw.pop()   #remove last empty item
        logbook =[]
        for record in raw:
            qso = {}
            tags = re.findall('<(.*?):(\d+).*?>([^<\t\n\r\f\v\Z]+)',record)
            for tag in tags:
                qso[tag[0].lower()] = tag[2][:int(tag[1])]
            logbook.append(qso)    
        return logbook
    
    def import_adif(self):
        """
        This function imports the results of a parsed ADIF file into the database.
        """
        fn = ""
        while fn == "":
            fn = raw_input("Please choose an ADIF file to import: ")
            if not os.path.isfile(fn):
                print("This file does not exist.")
                self.import_adif()
        log = self.adif_parse(fn)
        for key in self.import_fields:
                try:
                    self.c.execute("ALTER TABLE log ADD COLUMN {k} TEXT".format(k = key))
                except sqlite3.OperationalError:
                    pass
        self.db.commit()
        for qso in log:
            data_list = []
            for key in self.import_fields:
                if key.lower() in map(str.lower, qso):
                    data_list.append(qso[key.lower()])
                else:
                    data_list.append("")
            self.c.execute("INSERT INTO log {f} VALUES {d}".format(f = tuple(self.import_fields), d = tuple(data_list)))
            percent_done = float((log.index(qso) + 1)) / float(len(log)) * 100
            print("\rQSO record %i imported from %i QSO records (%i %% completed)" % ((log.index(qso) + 1), len(log), percent_done)),
        self.db.commit()
        log_menu.draw()

    def export_adif(self):
        header = "This ADIF file was created with SimPyL - The Simple Python Logger\n<adif_ver:5>2.2.7\n<eoh>\n"
        adif = self.name[:-3] + ".adi"
        f = open(home_folder + "/" + adif, "w")
        f.write(header)
        self.c.execute("""SELECT count(*) FROM log""")
        total = self.c.fetchall()[0][0]
        row = 0
        for qso in self.c.execute("""SELECT * FROM log"""):
            record = "\n"
            row += 1
            for k in qso.keys():
                if qso[k] != None and qso[k] != "":
                    record += "<%s:%s>%s" % (k.upper(), len(qso[k]), qso[k])
            record += "<eor>\n"
            f.write(record)
            percent_done = int(row / float(total) * float(100))
            print("\rQSO record %i exported from %i QSO records (%i %% completed)" % (row, total, percent_done)),
        f.close()
        log_menu.draw()

    def check(self, qso):
        for k in qso:
            if k == "QSO_DATE":
                if len(qso[k]) == 8:
                    continue
        pass

class Menu(object):
    """
    Menu class definition. This contains all of the attributes and methods that draw and control the menus. The name and options are provided when an instance is created.
    """
    def __init__(self, name, options):
        self.name = name
        self.options = options

    def draw(self):
        """
        This function draws the menu options, provides the user choice prompt and calls the appropriate function.
        """
        clear_screen()
        print("Callsign: %s --- Log File: %s" % (my_log.call, my_log.name))
        if self.name == "Log Menu":
            my_log.last_five()
        print("\n" + self.name + "\n" + "=" * 25)
        option_number = 1
        option_list = collections.OrderedDict()
        for option in self.options:
            option_list[str(option_number)] = option
            print(str(option_number) + " --- " + option)
            option_number += 1
        choice = raw_input("\nPlease choose an option ")
        if choice in option_list:
            self.options[option_list[choice]]()
        else:
            self.draw()

class Table(object):
    """
    Table class definition. This class controls how the tables that show QSOs(created through the PrettyTable library) are drawn.
    """
    def __init__(self, name, header, rows):
        self.name = name
        self.header = header
        self.rows = rows

    def draw(self):
        """
        This method draws the QSO tables.
        """
        print("\n" + self.name + "\n" + "=" * 25)
        qso_table = prettytable.PrettyTable()
        qso_table.field_names = self.header
        qso_table.rows = self.rows
        for row in self.rows:
            qso_table.add_row(row)
        return qso_table

# functions:

def enter():
    """
    This is a very simple function that prompts the user to press enter to continue.
    """
    choice = 0
    while choice != "":
        choice = raw_input("\nPlease press enter to continue ")

def clear_screen():
    """
    This function checks which OS you are using and sends the appropriate command to clear the screen.
    """
    if os.name == "nt":
        os.system("cls")
    else:
        os.system("clear")

def exit_simpyl():
    """
    This function prompts the user whether he really wants to quit, and prints a nice message if he does.
    """
    clear_screen()
    choice = ""
    while choice != "y" and choice != "n":
        choice = raw_input("Are you sure you want to quit SimPyL? (y/n): ")
    if choice == "n":
        start_main_menu()
    elif choice == "y":
        clear_screen()
        print("\nTank you for using SimPyL %s" % (simpyl_version))
        print("\n73 de VA2BBW!")
        print("\n--... ...--\n")
        sys.exit(0)
        
def simpyl_logo(fn):
    """
    This function displays the SimPyL ASCII-art logo at startup.
    """
    logo = open(fn).read().splitlines()
    for line in logo:
        print(line)

def about():
    """
    This function prints the main docstring.
    """
    clear_screen()
    print(__doc__)
    enter()
    start_main_menu()

def merge_adif():
    pass # This function takes two adif files and merges them together, testing for duplicates, and returns a new file.

def start():
    """
    This is the first function called by the main() function. It ends by calling the start_main_menu() method.
    """
    clear_screen()
    simpyl_logo(home_folder + "/" + "simpyl.logo.txt")
    print("\nWelcome to SimPyL %s\n" % (simpyl_version))
    my_log.choose_call()
    start_main_menu()

def start_main_menu():
    """
    This is a wrapper function used to perform any extra tasks before calling the main_menu.draw method.
    """
    main_menu.draw()

def start_log_menu():
    """
    This is a wrapper function used to perform any extra tasks before calling the log_menu.draw method.
    """
    while my_log.name == "":
        my_log.choose()
    my_log.connect()
    log_menu.draw()

def start_qsl_menu():
    """
    This is a wrapper function used to perform extra tasks before calling the qsl_menu.draw method.
    """
    qsl_menu.draw()

# Class instances

my_log = Log()

qsl_lotw = qsl.Lotw("%s/%s" % (home_folder, my_log.name)

qsl_eqsl = qsl.Eqsl("%s/%s" % (home_folder, my_log.name)

qsl_clublog = qsl.Clublog("%s/%s" % (home_folder, my_log.name)


main_menu = Menu(
    "Main Menu",
    collections.OrderedDict([
            ("Change your callsign", my_log.choose_call),
            ("Choose/change your log file", my_log.choose),
            ("Start logging", start_log_menu),
            ("About SimPyL", about),
            ("Exit SimPyL", exit_simpyl)
            ])
    )

log_menu = Menu (
    "Log Menu",
    collections.OrderedDict([
            ("Go back to main menu", start_main_menu),
            ("Import ADIF file to log", my_log.import_adif),
            ("Add a QSO", my_log.add_qso),
            ("Search for call", my_log.search_call),
            ("Go to QSL menu", start_qsl_menu),
            ("Export log to ADIF", my_log.export_adif),
            ("Exit SimPyL", exit_simpyl)
            ])
    )

qsl_menu = Menu(
    "QSL Menu",
    collections.OrderedDict([
            ("Go back to main menu", start_main_menu),
            ("Sign ADIF file (TQSL)", qsl_lotw.log_sign),
            ("Upload signed ADIF file to LoTW", qsl_lotw.log_upload),
            ("Upload ADIF file to eqsl.cc", qsl_eqsl.log_upload),
            ("Download QSLs from LoTW", qsl_lotw.log_download),
            ("Download QSLs from eqsl.cc", qsl_eqsl.log_download),
            ("Upload ADIF file to ClubLog", qsl_clublog.log_upload)
            ])
    )

# define main function

def main():
    try:
        start()
    except KeyboardInterrupt:
        exit_simpyl()
    except EOFError:
        exit_simpyl()

# This calls the functions to start the script

if __name__ == "__main__":
    main()
