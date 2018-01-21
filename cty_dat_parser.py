#! /usr/bin/python

# Title: cty_dat_parser
# Description: module to parse the cty.dat file
# Author: Ante Laurijssen VA2BBW <va2bbw@gmail.com>
# Date Created (yyyy-mm-dd): 2014-06-15
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
This module uses the cty.dat file to create a searchable database of location information
based on the callsign of the station. It can be used to fill out location info (like DXCC,
WPX, ITU, etc) automatically.
"""

# ============================================================================================================

# imports

from __future__ import absolute_import
import sqlite3
import os
import sys
import urllib
import re

# global variables

cty_dat_url = "http://www.country-files.com/cty/cty.dat"

# classes

class Cty_db(object):
    """
    This contains methods to create, and work with the db containing the info from cty.dat
    """
    def __init__(self, cty_file):
        self.cty_file = cty_file
        self.fields = ["DXCC_Name", "CQ_Zone", "ITU_Zone", "Cont", "Lat", "Long", "Main_Pref", "Other_Pref"]

    def cty_format(self):
        """
        This method formats the cty.dat file into something that can be added to a db file.
        """
        with open(self.cty_file, "r") as f:
            f = f.read().replace("\r", "").replace("\n", "").replace("\t", "")
            f = f.split(";")
            f2 = []
            f3 = []
            for dxcc in f:
                if not dxcc.strip():
                    f.remove(dxcc)
                else:
                    f[f.index(dxcc)] = "".join(dxcc.split()).split(":")
        for dxcc in f:
            x = dxcc[-1].split(",")
            if len(x) == 1:
                f2.append(dxcc)
            else:
                for pfx in x:
                    dxcc2 = list(dxcc)
                    dxcc2[-1] = pfx
                    f2.append(dxcc2)
        for line in f2:
            data = re.split(r"[(\[]", line[-1])
            if len(data) == 1:
                f3.append(line)
            else:
                line[-1] = data[0]
                for i in data[1:]:
                    if i.endswith(")"):
                        line[1] = i[:-1]
                    elif i.endswith("]"):
                        line[2] = i[:-1]
                        f3.append(line)
        return f3


    def connect(self, name):
        """
        This method connects to the database (creates it if it doesn't exist) and creates the cursor.
        """
        self.db = sqlite3.connect(name)
        self.db.row_factory = sqlite3.Row
        self.c = self.db.cursor()
        self.create_table()
        
    def create_table(self):
        """
        This creates the table for new database files if it doesn't exist.
        """
        self.c.execute("""CREATE TABLE IF NOT EXISTS cty(DXCC_Name TEXT COLLATE NOCASE, CQZ TEXT COLLATE NOCASE, ITUZ TEXT COLLATE NOCASE, CONT TEXT COLLATE NOCASE, Lat TEXT, Long TEXT, GMT_Offset TEXT, Main_PX TEXT COLLATE NOCASE, Other_PX TEXT COLLATE NOCASE)""")
        data = self.cty_format()
        self.c.execute("""SELECT * FROM cty""")
        if self.c.fetchone() is None:
            for dxcc in data:
                self.c.execute("INSERT INTO cty VALUES {d}".format(d = tuple(dxcc)))
            self.db.commit()
        
    def return_info(self, call):
        """
        This method will search for the call prefix in the database and return the corresponding 
        information.
        """
        self.call = call
        data = []
        l = []
        info = None
        for row in self.c.execute("""SELECT * FROM cty"""):
            if row["Other_PX"][1:] == self.call.upper():
                info = row
                break
            elif self.call.upper().startswith(row["Other_PX"]):
                data.append(row)
                l.append(len(row["Other_PX"]))
                info = data[l.index(max(l))]
        return info

# functions

def cty_download(url, folder):
    """
    This function downloads the cty.dat file from the web and saves it to the specified folder.
    """
    urllib.urlretrieve(url, folder + "/cty.dat")

# main function

def main():
    dat = Cty_db("cty.dat")
    dat.connect("cty.db")
    dat.create_table()
    info = (dat.return_info(raw_input("Please input callsign: ")))
    print(info)
    if info != None:
        print("==> %s <=== DXCC: %s CQ Zone: %s ITU Zone: %s " % (dat.call.upper(), info[7], info[1], info[2]))

# This calls the functions to start the script

if __name__ == "__main__":
    main()
            
            
            
