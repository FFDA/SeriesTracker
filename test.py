#!/usr/bin/python3

# This is the main program. From it all other modules will be access from now on.
# This file mainly contains menu options to access other parts of the program.

# Importing Python3 dependencies
import re
import os
import sys
import sqlite3
import textwrap # Wraps text to make it more presentable
import datetime # Used to compare the dates of the episode against the current date.

from imdbpie import Imdb # This is the dependency that is written by someone else and my program is based on it. It download information in JSON files from IMDB.

# Importing other programs modules writen by me.
from template import Templates
from add_show import AddShow 
from show_details import ShowDetails
import IMDB_id_validation as validate

# Assingning names to the modules.
template = Templates()
add_show = AddShow()
show_details = ShowDetails()

# Connecting to the database
dirname = os.path.dirname(__file__)
filename = os.path.join(dirname, 'shows.db')
con = sqlite3.connect(filename)
cur = con.cursor()

print(validate.check_if_input_contains_IMDB_id("tt5893860"))
